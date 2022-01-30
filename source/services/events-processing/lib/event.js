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
const event_schema = require('../config/event_schema.json');
const Ajv2020 = require('ajv/dist/2020');

const ajv = new Ajv2020();
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
  * @param {JSON} context - AWS Lambda invocation context (https://docs.aws.amazon.com/lambda/latest/dg/nodejs-context.html)
  */
  async processEvent(input, recordId, context) {
    const _self = this;
    try {
      // Extract event object and applicationId string from payload. application_id and event are required or record fails processing
      if(!input.hasOwnProperty('application_id')){
        return Promise.reject({
          recordId: recordId,
          result: 'ProcessingFailed',
          data: new Buffer.from(JSON.stringify(input) + '\n').toString('base64')
        });
      }
      if(!input.hasOwnProperty('event')){
        return Promise.reject({
          recordId: recordId,
          result: 'ProcessingFailed',
          data: new Buffer.from(JSON.stringify(input) + '\n').toString('base64')
        });
      }
      const applicationId = input.application_id;
      const event = input.event;
      
      // Add a processing timestamp and the Lambda Request Id to the event metadata
      let metadata = {
        ingestion_id: context.awsRequestId,
        processing_timestamp: moment().unix()
      };
      
      // If event came from Solution API, it should have extra metadata
      if (input.aws_ga_api_validated_flag) {
        metadata.api = {};
        if (input.aws_ga_api_requestId) { 
          metadata.api.request_id = input.aws_ga_api_requestId; 
          delete input.aws_ga_api_requestId;
        }
        if (input.aws_ga_api_requestTimeEpoch) {
          metadata.api.request_time_epoch = input.aws_ga_api_requestTimeEpoch;
          delete input.aws_ga_api_requestTimeEpoch;
        }
        delete input.aws_ga_api_validated_flag;
      }
      
      // Retrieve application config from Applications table
      const application = await _self.getApplication(applicationId);
      if (application !== null) {
        // Validate the input record against solution event schema
        const schemaValid = await _self.validateSchema(input);
        let transformed_event = {};
        if (schemaValid.validation_result == 'schema_mismatch') {
          metadata.processing_result = {
            status: 'schema_mismatch',
            validation_errors: schemaValid.validation_errors
          };
          transformed_event.metadata = metadata;
          //console.log(`Errors processing event: ${JSON.stringify(errors)}`);
        } else {
          metadata.processing_result = {
            status: 'ok'
          };
          transformed_event.metadata = metadata;
        }
        
        if(event.hasOwnProperty('event_id')){
          transformed_event.event_id = String(event.event_id);
        }
        if(event.hasOwnProperty('event_type')){
          transformed_event.event_type = String(event.event_type);
        }
        if(event.hasOwnProperty('event_name')){
          transformed_event.event_name = String(event.event_name);
        }
        if(event.hasOwnProperty('event_version')){
          transformed_event.event_version = String(event.event_version);
        }
        if(event.hasOwnProperty('event_timestamp')){
          transformed_event.event_timestamp = Number(event.event_timestamp);
        }
        if(event.hasOwnProperty('app_version')){
          transformed_event.app_version = String(event.app_version);
        }
        if(event.hasOwnProperty('event_data')){
          transformed_event.event_data = event.event_data;
        }
        
        transformed_event.application_name = String(application.application_name);
        transformed_event.application_id = String(applicationId);
        
        return Promise.resolve({
          recordId: recordId,
          result: 'Ok',
          data: new Buffer.from(JSON.stringify(transformed_event) + '\n').toString('base64')
        });
      } else {
        /**
         * Handle events from unregistered ("NOT_FOUND") applications
         * Sets processing result as "unregistered"
         * We don't attempt to validate schema of unregistered events, we just coerce the necessary fields into expected format 
         */
        metadata.processing_result = {
          status: 'unregistered'
        };
        let unregistered_format = {};
        unregistered_format.metadata = metadata;
        
        if(event.hasOwnProperty('event_id')){
          unregistered_format.event_id = String(event.event_id);
        }
        if(event.hasOwnProperty('event_type')){
          unregistered_format.event_type = String(event.event_type);
        }
        if(event.hasOwnProperty('event_name')){
          unregistered_format.event_name = String(event.event_name);
        }
        if(event.hasOwnProperty('event_version')){
          unregistered_format.event_version = String(event.event_version);
        }
        if(event.hasOwnProperty('event_timestamp')){
          unregistered_format.event_timestamp = Number(event.event_timestamp);
        }
        if(event.hasOwnProperty('app_version')){
          unregistered_format.app_version = String(event.app_version);
        }
        if(event.hasOwnProperty('event_data')){
          unregistered_format.event_data = event.event_data;
        }
        
        // Even though the application_id is not registered, let's add it to the event
        unregistered_format.application_id = String(applicationId);
        
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
        return Promise.resolve({
          validation_result: 'schema_mismatch',
          validation_errors: errors
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