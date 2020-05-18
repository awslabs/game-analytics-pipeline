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
const moment = require('moment');
const AWS = require('aws-sdk');
const cloudwatch = new AWS.CloudWatch();
const creds = new AWS.EnvironmentCredentials('AWS'); // Lambda provided credentials
const cloudwatchConfig = {
	credentials: creds,
	region: process.env.AWS_REGION
};

/**
 * Process Kinesis Analytics output and publish to CloudWatch
 * @class CloudWatchMetrics
 */
class CloudWatchMetrics {
    constructor() {
        this.cloudwatchConfig = cloudwatchConfig;
    }
    
    /**
     * Publish metric to CloudWatch Metrics
     * @param {JSON} metric - the payload to send to Cloudwatch
     */
    async publishMetric(metric) {
        let namespace = `${process.env.CW_NAMESPACE}`;
        console.log(`Publishing metric: ${JSON.stringify(metric)}`);
        const params = {
            'MetricData': [metric],
            'Namespace': namespace
        };
        let data;
        try {
            data = await cloudwatch.putMetricData(params).promise();
            console.log(`cw response: ${JSON.stringify(data)}`);
        } catch (err) {
            console.log(`${JSON.stringify(err)}`);
            return Promise.reject(err);
        }
        return Promise.resolve(data);
    }
    
    /**
     * Convert a Kinesis Data Analytics output metric record into CloudWatch Metric format
     * @param {JSON} payload - input metric data record to be transformed
     */
    async buildMetric(payload) {
        let metric = {
            MetricName: payload.METRIC_NAME,
            Timestamp: moment(payload.METRIC_TIMESTAMP).unix(),
            Value: payload.METRIC_UNIT_VALUE_INT,
            Unit: payload.METRIC_UNIT || 'None'
        };
        
        // Extract dimensions from input, populate dimensions array in format required by CloudWatch
        // Strip DIMENSION_ prefix from metric before publishing
        let dimensions = [];
        for (var key in payload) {
        	if (key.includes('DIMENSION_') && (payload[key] !== null && payload[key] != "" && payload[key] != "null")) {
                dimensions.push({
                    'Name': key.split("DIMENSION_").pop(),
                    'Value': payload[key]
                });
        	}
        }
        if (dimensions.length > 0) {
            metric.Dimensions = dimensions;
        }
        return Promise.resolve(metric);
    }
}

module.exports = CloudWatchMetrics;