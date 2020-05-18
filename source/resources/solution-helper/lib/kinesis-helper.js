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

/**
 * Helper function to interact with Kinesis for cfn custom resource.
 *
 * @class kinesisHelper
 */
class kinesisHelper {
  /**
   * @class kinesisHelper
   * @constructor
   */
  constructor() {
    this.creds = new AWS.EnvironmentCredentials('AWS'); // Lambda provided credentials
    this.config = {
      credentials: this.creds,
      region: process.env.AWS_REGION,
    };
  }
  
  startKinesisAnalyticsApp(applicationName) {
    return new Promise((resolve, reject) => {
      let params = {
        ApplicationName: applicationName
      };
      
      console.log(`Attempting to start Kinesis Analytics App: ${JSON.stringify(params)}`);
      let kda = new AWS.KinesisAnalytics(this.config);
      
      kda.describeApplication(params, function(err, response) {
        if (err) {
          console.log(JSON.stringify(err));
          reject(err);
        } else {
          if (response == null) {
            console.log('The Kinesis Analytics application could not be found');
            reject(err);
          }
          if (response.ApplicationDetail.ApplicationStatus === 'READY') {
            let params = {
              ApplicationName: applicationName,
              InputConfigurations: [
                {
                  'Id': '1.1',
                  'InputStartingPositionConfiguration': {
                    'InputStartingPosition': 'NOW'
                  }
                }
              ]
            };
            console.log('Starting Kinesis Analytics Application');
            kda.startApplication(params, function(err, response) {
              if (err) {
                console.log(JSON.stringify(err));
                reject(err);
              } else {
                console.log('Started Kinesis Analytics Application');
                resolve(response);
              }
            });
          }
        }
      });
    });
  }
}

module.exports = kinesisHelper;
