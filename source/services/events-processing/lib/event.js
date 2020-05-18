/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: MIT-0
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy of this
 * software and associated documentation files (the "Software"), to deal in the Software
 * without restriction, including without limitation the rights to use, copy, modify,
 * merge, publish, distribute, sublicense, and/or sell copies of the Software, and to
 * permit persons to whom the Software is furnished to do so.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
 * INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A
 * PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
 * HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
 * OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
 * SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
 */
 
'use strict';

const AWS = require('aws-sdk');
const _ = require('underscore');
const moment = require('moment');
const { v4: uuidv4 } = require('uuid');
const event_schema = require('../config/event_schema.json');
const Ajv = require('ajv');

const ajv = new Ajv({schemaId: 'auto'});
ajv.addMetaSchema(require('ajv/lib/refs/json-schema-draft-04.json'));
var validate = ajv.compile(event_schema);

const creds = new AWS.EnvironmentCredentials('AWS'); // Lambda provided credentials
const dynamoConfig = {
  credentials: creds,
  region: process.env.AWS_REGION
};

console.log(`Loaded event JSON Schema: ${JSON.stringify(event_schema)}`);

class Event {
  
  constructor() {
    this.dynamoConfig = dynamoConfig;
  }

  /**
  * Process an event record sent to the events stream
  * Format processing output in format required by Kinesis Firehose
  * @param {JSON} input - game event input payload
  * @param {string} recordId - recordId from Kinesis
  */
  async processEvent(input, recordId) {
    const _self = this;
    try {
      
      // Extract event object and applicationId string from payload
      const applicationId = input.application_id;
      const event = input.event;
      // Build metadata to attach to transformed event, including a unique ingestion_id
      let metadata = {
        ingestion_id: uuidv4(),
        processing_timestamp: moment().unix()
      };
      
      // If event came from Solution API, it should have extra metadata
      // Add sourceIp, requestId and requestTime 
      if (input.aws_ga_api_validated_flag) {
        metadata.api = {};
        if (input.aws_ga_api_requestId) { 
          metadata.api.request_id = input.aws_ga_api_requestId; 
        }
        if (input.aws_ga_api_requestTimeEpoch) {
          metadata.api.request_time_epoch = input.aws_ga_api_requestTimeEpoch;
        }
        if (input.aws_ga_api_sourceIp) {
          metadata.api.source_ip = input.aws_ga_api_sourceIp;
        }
      }
      
      // Retrieve application config from Applications table
      const application = await _self.getApplication(applicationId);
      if (application !== null) {
        // Validate the input record against solution event schema
        const schemaValid = await _self.validateSchema(input);
        if (!schemaValid) {
          let errors = validate.errors;
          /**
           * Transform schema mismatch events into custom event format
           */
          metadata.processing_result = {
            status: 'schema_mismatch'
          };
          let custom_event_format = {
            application_id: applicationId,
            application_name: application.application_name,
            metadata: metadata,
            custom_event: event
          };
          console.log(`Errors processing event: ${JSON.stringify(errors)}`);
          return Promise.resolve({
            recordId: recordId,
            result: 'Ok',
            data: new Buffer.from(JSON.stringify(custom_event_format) + '\n').toString('base64')
          });
        } else {
          
          /**
           * Generate standard event format populated with validated fields
           */
          metadata.processing_result = {
            status: 'ok'
          };
          let standard_format = {
            event_id: event.event_id,
            event_type: event.event_type,
            event_name: event.event_name,
            event_version: event.event_version,
            event_timestamp: event.event_timestamp,
            client_id: event.client_id,
            event_data: event.event_data,
            user_id: event.user_id,
            session_id: event.session_id,
            application_name: application.application_name,
            application_id: applicationId,
            metadata: metadata
          };
          return Promise.resolve({
            recordId: recordId,
            result: 'Ok',
            data: new Buffer.from(JSON.stringify(standard_format) + '\n').toString('base64')
          });
        }
      } else {
        /**
         * Handle events from unregistered ("NOT_FOUND") applications
         * Sets processing result as "unregistered"
         * Stores raw event data as "custom_event" and don't validate event
         */
        metadata.processing_result = {
          status: 'unregistered'
        };
        let unregistered_format = {
          application_id: applicationId,
          metadata: metadata,
          custom_event: event
        };
        return Promise.resolve({
          recordId: recordId,
          result: 'Ok',
          data: new Buffer.from(JSON.stringify(unregistered_format) + '\n').toString('base64')
        });
      } 
    } catch (err) {
      console.log(`Error processing record: ${JSON.stringify(err)}`);
      return Promise.reject({
        recordId: recordId,
        result: 'ProcessingFailed',
        data: new Buffer.from(JSON.stringify(input) + '\n').toString('base64')
      });
    }
  }
  
  /**
   * Retrieve application from DynamoDB
   * Fetches from and updates the local registered applications cache with results
   */
  async getApplication(applicationId) {
    const params = {
      TableName: process.env.APPLICATIONS_TABLE,
      Key: {
        application_id: applicationId
      }
    };
    
    // first try to fetch from cache
    let applicationsCacheResult = global.applicationsCache.get(applicationId);
    if (applicationsCacheResult == 'NOT_FOUND') {
      // if already marked not found, skip processing. Applications will remain "NOT_FOUND" until the cache refresh
      return Promise.resolve(null);
    } else if (applicationsCacheResult == undefined) {
      // get from DynamoDB and set in Applications cache
      const docClient = new AWS.DynamoDB.DocumentClient(this.dynamoConfig);
      try {
        let data = await docClient.get(params).promise();
        if (!_.isEmpty(data)) {
          // if found in ddb, set in cache and return it
          global.applicationsCache.set(applicationId, data.Item);
          return Promise.resolve(data.Item);
        } else {
          // if application isn't registered in dynamodb, set not found in cache
          console.log(`Application ${applicationId} not found in DynamoDB`);
          global.applicationsCache.set(applicationId, 'NOT_FOUND');
          return Promise.resolve(null);
        }
      } catch (err) {
        console.log(JSON.stringify(err));
        return Promise.reject(err);
      }
    } else {
      // if in cache, return it
      return Promise.resolve(applicationsCacheResult);
    }
  }
  
  /**
   * Validate input data against JSON schema
   */
  async validateSchema(data) {
    try {
      let valid = validate(data);
      if (!valid) {
        let errors = validate.errors;
        console.log(`Schema valiidation error: ${JSON.stringify(errors)}`);
        return Promise.resolve({
          validation_result: 'failed'
        });
      } else {
        return Promise.resolve({
          validation_result: 'ok'
        });
      }
    } catch (err) {
      console.log(`There was an error validating the schema ${JSON.stringify(err)}`);
      return Promise.reject(err);
    }
  }
}


module.exports = Event;