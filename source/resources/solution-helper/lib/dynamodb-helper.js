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

let AWS = require('aws-sdk');
const _ = require('underscore');

/**
 * Helper function to interact with dynamodb for cfn custom resource.
 *
 * @class dynamoDBHelper
 */
class dynamoDBHelper {
  /**
   * @class dynamoDBHelper
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
   * Save item to DynamoDB
   */
  saveItem(item, ddbTable) {
    // Handling Promise Rejection
    console.log(`Saving item to DynamoDB: ${JSON.stringify(item)}`);
    process.on('unhandledRejection', error => {
      throw error;
    });

    return new Promise((resolve, reject) => {
      for (var i = 0; i < _.keys(item).length; i++) {
        item[_.keys(item)[i]] = this._checkAssignedDataType(
          item[_.keys(item)[i]]
        );
      }

      let params = {
        TableName: ddbTable,
        Item: item
      };

      const docClient = new AWS.DynamoDB.DocumentClient(this.config);
      docClient.put(params, function (err, resp) {
        if (err) {
          console.log(JSON.stringify(err));
          reject(err);
        } else {
          console.log(`Item saved.`);
          resolve(item);
        }
      });
    });
  }

  _checkAssignedDataType(attr) {
    if (_.isObject(attr)) {
      if (_.has(attr, 'N')) {
        return parseInt(attr['N']);
      } else if (_.has(attr, 'B')) {
        return attr['B'] === 'true';
      } else {
        for (var i = 0; i < _.keys(attr).length; i++) {
          attr[_.keys(attr)[i]] = this._checkAssignedDataType(
            attr[_.keys(attr)[i]]
          );
        }
        return attr;
      }
    } else {
      return attr;
    }
  }
}

module.exports = dynamoDBHelper;
