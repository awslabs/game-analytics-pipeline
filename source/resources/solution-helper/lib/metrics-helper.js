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

const requestPromise = require('request-promise');

// Metrics class for sending usage metrics to solution endpoints
class Metrics {
  constructor() {
    this.endpoint = 'https://metrics.awssolutionsbuilder.com/generic';
  }
  
  async sendAnonymousMetric(metric) {
    const options = {
      uri: this.endpoint,
      port: 443,
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: metric,
      json: true
    };
  
    try {
      const result = await requestPromise(options);
      return Promise.resolve(result);
    } catch (err) {
      console.log(`Error sending metric, skipped: ${JSON.stringify(err)}`);
      return Promise.resolve(metric);
    }
  }
}

module.exports = Metrics;
