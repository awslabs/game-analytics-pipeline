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
 * Helper function to interact with S3 for cfn custom resource.
 *
 * @class s3Helper
 */
class s3Helper {
  /**
   * @class s3Helper
   * @constructor
   */
  constructor() {
    this.creds = new AWS.EnvironmentCredentials('AWS'); // Lambda provided credentials
  }
  
  getObject(s3Bucket, s3Key) {
    return new Promise((resolve, reject) => {
      try {
        let s3 = new AWS.S3({sslEnabled: true, signatureVersion: 'v4'});
        let params = {
          Bucket: s3Bucket,
          Key: s3Key
        };
        
        s3.getObject(params, function(err, data) {
          if (err) {
            console.log(JSON.stringify(err));
            reject(err);
          } else {
            var object = data.Body.toString();
            console.log(`Retrieved data from S3: ${JSON.stringify(object)}`);
            resolve(object);
          }
        });
      } catch (err) {
        console.log(JSON.stringify(err));
        reject(err);
      }
    });
  }
  
  uploadObject(s3Bucket, s3Key, objectBody) {
    console.log(`Uploading object to s3://${s3Bucket}/${s3Key}`);
    return new Promise((resolve, reject) => {
      let s3 = new AWS.S3({sslEnabled: true, signatureVersion: 'v4'});
      const params = {
        Body: objectBody,
        Bucket: s3Bucket,
        Key: s3Key,
        ServerSideEncryption: 'AES256'
      };
  
      s3.putObject(params, function(err, data) {
        if (err) {
          console.log(err);
          reject(err);
        } else {
          console.log(JSON.stringify(data));
          resolve(data);
        }
      });
    });
  }
}

module.exports = s3Helper;
