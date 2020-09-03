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

/**
 * Lib
 */

const AWS = require('aws-sdk');
const NodeCache = require( 'node-cache');
const Event = require('./event.js');

/**
 * Applications table results cache
 * Maintains a local cache of registered Applications in DynamoDB. 
 */
global.applicationsCache = new NodeCache({stdTTL: process.env.CACHE_TIMEOUT_SECONDS, checkPeriod: 60, maxKeys: 1000, useClones: false});

const respond = async (event, context) => {
  let validEvents = 0;
  let invalidEvents = 0;
  let results = [];
  let _event = new Event();
  
  for (const record of event.records) {
    try {
      // Kinesis data is base64 encoded so decode here
      const payload = JSON.parse(Buffer.from(record.data, 'base64'));
      const processEvent = await _event.processEvent(payload, record.recordId, context);
      if (processEvent.result === 'Ok') {
        validEvents++;
      } else {
        invalidEvents++;
      }
      results.push(processEvent);
    } catch (err) {
      console.log(JSON.stringify(err));
      invalidEvents++;
      results.push({
        recordId: record.recordId,
        result: 'ProcessingFailed',
        data: record.data
      });
    }
  }
  console.log(JSON.stringify({
    'InputEvents': event.records.length,
    'EventsProcessedStatusOk': validEvents,
    'EventsProcessedStatusFailed': invalidEvents
  }));
  return Promise.resolve({
    records: results
  });
};

module.exports = {
  respond
};