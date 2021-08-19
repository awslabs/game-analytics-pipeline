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

const https = require('https');

// Metrics class for sending usage metrics to solution endpoints
class Metrics {
  constructor() {
    this.endpoint = 'https://metrics.awssolutionsbuilder.com/generic';
  }
  
  async sendAnonymousMetric(metric) {
    console.log('RESPONSE BODY:\n', responseBody); 
    const parsedUrl = url.parse(event.ResponseURL); 
    const options = { 
        hostname: this.endpoint, 
        port: 443,
        method: 'POST', 
        headers: { 
            'Content-Type': 'application/json', 
            'Content-Length': metric.length, 
        } 
    }; 
 
    const req = https.request(options, (res) => { 
        console.log('STATUS:', res.statusCode); 
        console.log('HEADERS:', JSON.stringify(res.headers)); 
        callback(null, 'Successfully sent stack response!'); 
    }); 
 
    req.on('error', (err) => { 
        console.log('sendResponse Error:\n', err); 
        callback(err); 
    }); 
 
    req.write(JSON.stringify(metric)); 
    req.end();
  }
}

module.exports = Metrics;
