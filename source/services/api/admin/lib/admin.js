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
const crypto = require("crypto");

/**
 * Performs admin actions including creating, retrieving and deleting
 * applications within the solution
 *
 * @class Application
 */
class Application {
  /**
   * @class Application
   * @constructor
   */
  constructor() {
    this.creds = new AWS.EnvironmentCredentials('AWS'); // Lambda provided credentials
    this.config = {
      credentials: this.creds,
      region: process.env.AWS_REGION,
    };
  }
  
  /**
   * Creates a new application
   * @param {JSON} application - Object representing the application configuration
   */
  async createApplication(application) {
    console.log(`Creating application`);
    try {
      const applicationId = uuidv4();
      const updatedAt = moment().utc().format();
      const params = {
        TableName: process.env.APPLICATIONS_TABLE,
        Item: {
          'application_name': application.Name,
          'description': application.Description,
          'updated_at': updatedAt,
          'created_at': updatedAt,
          'application_id': applicationId
        }
      };
      const docClient = new AWS.DynamoDB.DocumentClient(this.config);
      await docClient.put(params).promise();
      return Promise.resolve({
        'ApplicationId': applicationId,
        'ApplicationName': application.Name,
        'Description': application.Description,
        'UpdatedAt': updatedAt,
        'CreatedAt': updatedAt
      });
    } catch (err) {
      console.log(JSON.stringify(err));
      return Promise.reject({
        code: 500,
        error: 'InternalFailure',
        message: `Error occurred while attempting to create application`
      });
    }
  }
  
  /**
   * List all applications
   * Scans DynamoDB to retrieve all applications
   */
  async listApplications() {
    let params = {
      TableName: process.env.APPLICATIONS_TABLE
    };
    let length = 0;
    let docClient = new AWS.DynamoDB.DocumentClient(this.config);
    try {
      let result = await docClient.scan(params).promise();
      length += result.Items.length;
      if (length < 1){
        return Promise.reject({
          code: 404,
          error: 'NotFoundException',
          message: 'No applications are registered with the solution.'
        });
      } else {
        let results = [];
        result.Items.forEach(function(item) {
          results.push({
            'ApplicationId': item.application_id,
            'ApplicationName': item.application_name,
            'Description': item.description,
            'UpdatedAt': item.updated_at,
            'CreatedAt': item.created_at
          });  
        });
        return Promise.resolve({
          "Applications": results,
          "Count": length
        });
      }
    } catch (err) {
      console.log(JSON.stringify(err));
      return Promise.reject({
        code: 500,
        error: 'InternalFailure',
        message: 'Error occurred while attempting to retrieve applications',
      });
    }
  }

  /**
   * Retrieves an application detail
   * @param {string} applicationId - The application identifier 
   */
  async getApplicationDetail(applicationId) {
    const params = {
      TableName: process.env.APPLICATIONS_TABLE,
      Key: {
        application_id: applicationId
      }
    };

    const docClient = new AWS.DynamoDB.DocumentClient(this.config);
    try {
      let data = await docClient.get(params).promise();
      if (!_.isEqual(data, {})) {
        let response = {
          'ApplicationId': data.Item.application_id,
          'ApplicationName': data.Item.application_name,
          'CreatedAt': data.Item.created_at,
          'Description': data.Item.description,
          'UpdatedAt': data.Item.updated_at
        };
        console.log(JSON.stringify(response));
        return Promise.resolve(response);
      } else {
        return Promise.reject({
          code: 404,
          error: 'NotFoundException',
          message: `The application does not exist.`
        });
      }
      
    } catch (err) {
      console.log(JSON.stringify(err));
      return Promise.reject({
        code: 500,
        error: 'InternalFailure',
        message: `Error occurred while attempting to retrieve application`
      });
    }
  }

  
  /**
   * List application event endpoint authorizations
   */
  async listApplicationAuthorizations(applicationId) {
    try {
      let result = this._listApplicationAuthorizations(applicationId);
      return Promise.resolve(result);
    } catch (err) {
      console.log(JSON.stringify(err));
      return Promise.reject({
        code: 500,
        error: 'InternalFailure',
        message: `Error occurred while attempting to retrieve application`
      });
    }
  }
  
  /**
   * List application authorizations
   * Query authorizations index to get authorizations for application
   */
  async _listApplicationAuthorizations(applicationId, lastevalkey) {
    let applicationAuthorizations = [];
    let params = {
      TableName: process.env.AUTHORIZATIONS_TABLE,
      IndexName: 'ApplicationAuthorizations',
      KeyConditionExpression: 'application_id = :appId',
      ExpressionAttributeValues: {
        ':appId': applicationId
      },
      Limit: 500
    };
    
    if (lastevalkey) {
      params.ExclusiveStartKey = lastevalkey;
    }
    let docClient = new AWS.DynamoDB.DocumentClient(this.config);
    try {
      let result = await docClient.query(params).promise();
      result.Items.forEach(function(item) {
        applicationAuthorizations.push({
          'ApiKeyId': item.api_key_id,
          'ApiKeyDescription': item.api_key_description,
          'ApiKeyName': item.api_key_name,
          'ApiKeyValue': item.api_key_value,
          'ApplicationId': item.application_id,
          'UpdatedAt': item.updated_at,
          'CreatedAt': item.created_at,
          'Enabled': item.enabled
        });  
        
      });
      
      // If there is more data, load more data and append them to authorizations
      if (result.LastEvaluatedKey) {
        let moreResult = await this._listApplicationAuthorizations(applicationId, lastevalkey);
        moreResult.Items.forEach(function(item) {
          applicationAuthorizations.push({
            'ApiKeyId': item.api_key_id,
            'ApiKeyDescription': item.api_key_description,
            'ApiKeyName': item.api_key_name,
            'ApiKeyValue': item.api_key_value,
            'ApplicationId': item.application_id,
            'UpdatedAt': item.updated_at,
            'CreatedAt': item.created_at,
            'Enabled': item.enabled
          });
        });
      }
      
      return Promise.resolve({
        'Authorizations': applicationAuthorizations,
        'Count': applicationAuthorizations.length
      });
    } catch (err) {
      return Promise.reject(err);
    }
  }
  
  /**
   * Deletes an application from the solution
   * @param {string} applicationId - The unique identifier for the application
   */
  async deleteApplication(applicationId) {
    try {
      await this._deleteApplicationAuthorizations(applicationId);
      await this._deleteApplication(applicationId);
      
      return Promise.resolve('Delete successful');
    } catch (err) {
      return Promise.reject(err);
    } 
  }
  
  /**
   * Passes through idempotency behavior of DynamoDB DeleteItem API.
   * Items that don't exist will still return 200 as deleted
   */
  async _deleteApplication(applicationId) {
    const params = {
      TableName: process.env.APPLICATIONS_TABLE,
      Key: {
        application_id: applicationId
      }
    };

    const docClient = new AWS.DynamoDB.DocumentClient(this.config);
    try {
      let data = await docClient.delete(params).promise();
      return Promise.resolve(data);
    } catch (err) {
      console.log(JSON.stringify(err));
      return Promise.reject({
        code: 500,
        error: 'InternalFailure',
        message: `Error occurred while attempting to delete application`
      });
    }
  }
  
  /**
   * Queries ApplicationAuthorizations DynamoDB GSI index and deletes all the api key authorizations for an application
   */
  async _deleteApplicationAuthorizations(applicationId) {
    const docClient = new AWS.DynamoDB.DocumentClient(this.config);
    try {
      // Lookup authorizations associated with application
      let authorizationResults = await docClient.query({
        TableName: process.env.AUTHORIZATIONS_TABLE,
        IndexName: process.env.APPLICATION_AUTHORIZATIONS_INDEX,
        KeyConditionExpression: 'application_id = :appId',
        ExpressionAttributeValues: {
          ':appId': applicationId
        },
        ProjectionExpression: 'api_key_id'
      }).promise();
      
      if (authorizationResults.Items.length === 0) {
        console.log(`No authorizations for this application`);
        return Promise.resolve(true);
      }
      for (const item of authorizationResults.Items) {
        await this.deleteAuthorization(item.api_key_id, applicationId); 
      }
      return Promise.resolve(true);
    } catch (err) {
      console.log(JSON.stringify(err));
      return Promise.reject({
        code: 500,
        error: 'InternalFailure',
        message: `Error occurred while attempting to delete application`
      });
    }
  }
  
  /**
   * Register API Key authorization with Authorizations DynamoDB Table
   * @param {string} apiKey - Authorization value to allow access to the registered application
   * @param {string} applicationId - ApplicationId to create authorization for
   * @param {string} apiKeyName - The name provided for the api key 
   * @param {string} apiKeyDescription - The description for the api key
   * @param {string} apikeyId - The key identifier
   */
  async createAuthorization(apiKeyValue, applicationId, apiKeyName, apiKeyDescription, apiKeyId) {
    try {
      const docClient = new AWS.DynamoDB.DocumentClient(this.config);
      const updated_at = moment().utc().format();
      const created_at = moment().utc().format();
      const params = {
        TableName: process.env.AUTHORIZATIONS_TABLE,
        Item: {
          api_key_id: apiKeyId,
          application_id: applicationId,
          api_key_name: apiKeyName,
          api_key_value: apiKeyValue,
          api_key_description: apiKeyDescription,
          updated_at: updated_at,
          created_at: created_at,
          enabled: true
        }
      };
      await docClient.put(params).promise();
      const response = {
        ApiKeyId: params.Item.api_key_id,
        ApiKeyValue: params.Item.api_key_value,
        ApiKeyName: apiKeyName,
        ApplicationId: applicationId,
        ApiKeyDescription: apiKeyDescription,
        CreatedAt: created_at,
        UpdatedAt: updated_at,
        Enabled: true
      };
      return Promise.resolve(response);
    } catch (err) {
      console.log(JSON.stringify(err));
      return Promise.reject({
        code: 500,
        error: 'InternalFailure',
        message: `Error creating authorization`
      });
    }
  }
  
  /**
   * Get authorization details
   * @param {string} apiKeyId - The api key id
   * @param {string} applicationId - Application associated with the authorization
   */
  async getAuthorizationDetail(apiKeyId, applicationId) {
    const params = {
      TableName: process.env.AUTHORIZATIONS_TABLE,
      Key: {
        api_key_id: apiKeyId,
        application_id: applicationId
      }
    };

    const docClient = new AWS.DynamoDB.DocumentClient(this.config);
    try {
      let data = await docClient.get(params).promise();
      if (!_.isEqual(data, {})) {
        let result = {
          ApiKeyId: data.Item.api_key_id,
          ApiKeyName: data.Item.api_key_name,
          ApiKeyDescription: data.Item.api_key_description,
          ApiKeyValue: data.Item.api_key_value,
          ApplicationId: data.Item.application_id,
          CreatedAt: data.Item.created_at,
          UpdatedAt: data.Item.updated_at,
          Enabled: data.Item.enabled
        };
        return Promise.resolve(result);
      } else {
        console.log(`MissingAuthorization: Authorization not found`);
        return Promise.reject({
          code: 404,
          error: 'NotFoundException',
          message: `Authorization not found`
        });
      }
    } catch (err) {
      console.log(JSON.stringify(err));
      return Promise.reject({
        code: 500,
        error: 'InternalFailure',
        message: `Error occurred while attempting to retrieve application`
      });
    }
  }
  
  /**
   * Modify an API Key authorization in DynamoDB. 
   * Currently only supports updating enabled status. 
   * @param {string} applicationId - ApplicationId
   * @param {string} apikeyId - The key identifier
   * @param {boolean} enabled - API Key status in the solution (true/false)
   */
  async modifyAuthorization(apiKeyId, applicationId, enabled) {
    try {
      const docClient = new AWS.DynamoDB.DocumentClient(this.config);
      const updated_at = moment().utc().format();
      const params = {
        TableName: process.env.AUTHORIZATIONS_TABLE,
        Key: {
          api_key_id: apiKeyId,
          application_id: applicationId
        },
        UpdateExpression: "set enabled = :enabled, updated_at = :updated_at",
        ExpressionAttributeValues: {
            ":enabled": enabled,
            ":updated_at": updated_at
        },
        ReturnValues: 'ALL_NEW',
      };
      const response = await docClient.update(params).promise();
      return Promise.resolve({
        ApiKeyId: response.Attributes.api_key_id,
        ApiKeyName: response.Attributes.api_key_name,
        ApiKeyDescription: response.Attributes.api_key_description,
        ApiKeyValue: response.Attributes.api_key_value,
        ApplicationId: response.Attributes.application_id,
        CreatedAt: response.Attributes.created_at,
        UpdatedAt: response.Attributes.updated_at,
        Enabled: response.Attributes.enabled
      });
    } catch (err) {
      console.log(JSON.stringify(err));
      return Promise.reject({
        code: 500,
        error: 'InternalFailure',
        message: `Error modifying authorization`
      });
    }
  }
  
  /**
   * Deletes authorization from the solution authorizations table
   * @param {string} apiKeyId - The api key Id
   * @param {string} applicationId - The unique identifier for the application the authorization is associated with.
   */
  async deleteAuthorization(apiKeyId, applicationId) {
    try {
      await this._deleteAuthorization(apiKeyId, applicationId);
      return Promise.resolve({Result: 'Deleted'});
    } catch (err) {
      console.log(JSON.stringify(err));
      return Promise.reject(err);
    } 
  }
  
  
  /**
   * Passes through idempotency behavior of DynamoDB DeleteItem API.
   * Items that don't exist will still return 200 as deleted
   */
  async _deleteAuthorization(apiKeyId, applicationId) {
    const params = {
      TableName: process.env.AUTHORIZATIONS_TABLE,
      Key: {
        api_key_id: apiKeyId,
        application_id: applicationId
      },
      ReturnValues: 'ALL_OLD'
    };

    const docClient = new AWS.DynamoDB.DocumentClient(this.config);
    try {
      let data = await docClient.delete(params).promise();
      return Promise.resolve(data);
    } catch (err) {
      console.log(JSON.stringify(err));
      return Promise.reject({
        code: 500,
        error: 'InternalFailure',
        message: `Error occurred while attempting to delete authorization`
      });
    }
  }
  
  
  /**
   * Create a new api key
   * @param {string} apiKeyName - Name to associate with the newly created key
   * @param {string} apiKeyDescription - Description for the key
   */
  async createApiKey(apiKeyName, apiKeyDescription) {
    console.log(`Creating ApiKey`);
    const params = {};
    params.enabled = true;
    
    if (apiKeyDescription) {
      params.description = apiKeyDescription;
    } else {
      params.description = `Auto-generated api key`;
    }
    
    if (apiKeyName) {
      params.name = apiKeyName;
    } else {
      params.name = 'default';
    }
    
    try {
      let response = {
        id: uuidv4(),
        value: crypto.randomBytes(64).toString('base64'),
        description: params.description,
        name: params.name,
        enabled: params.enabled
      };
      return Promise.resolve(response);
    } catch (err) {
      console.log(JSON.stringify(err));
      return Promise.reject({
        code: 500,
        error: 'InternalFailure',
        message: `Error occurred while creating API Key`
      });
    }
  }
}

module.exports = Application;

