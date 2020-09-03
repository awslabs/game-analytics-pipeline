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
 * Helper function to interact with CloudWatch for cfn custom resource.
 *
 * @class cloudwatchHelper
 */
class cloudwatchHelper {
  /**
   * @class cloudwatchHelper
   * @constructor
   */
  constructor() {
    this.creds = new AWS.EnvironmentCredentials('AWS'); // Lambda provided credentials
    this.config = {
      credentials: this.creds,
      region: process.env.AWS_REGION,
    };
  }

  deleteDashboard(dashboardName) {
    return new Promise((resolve, reject) => {
      let cloudwatch = new AWS.CloudWatch(this.config);
      const params = {
        DashboardNames: [
          dashboardName
        ]
      };

      cloudwatch.deleteDashboards(params, function(err, data) {
        if (err) {
          console.log(JSON.stringify(err));
          reject(err);
        } else {
          console.log(data);
          resolve(data);
        }
      })
    })
  }

  createDashboard(event) {
    let cloudwatch = new AWS.CloudWatch(this.config);
    console.log(`Generate dashboard with input params: ${JSON.stringify(event)}`);
    let widgets = [];
    // Dashboard Header
    widgets.push({
      type: 'text',
      x: 0,
      y: 0,
      width: 24,
      height: 2,
      properties: {
        markdown: '\n# **Game Analytics Pipeline - Operational Health**\nThis dashboard contains operational metrics for the Game Analytics Pipeline. Use these metrics to help you monitor the operational status of the AWS services used in the solution and track important application metrics.\n'
      }
    });

    // Stream Ingestion and Processing Header
    widgets.push({
      type: 'text',
      x: 0,
      y: 2,
      width: 12,
      height: 3,
      properties: {
        markdown: `\n## Stream Ingestion & Processing\nThis section covers metrics related to ingestion of data into the solution's Events Stream and processing by Kinesis Data Firehose and AWS Lambda Events Processing Function. Use the metrics here to track data freshness/latency and any issues with processor throttling/errors. \n`
      }
    });
    
    // Events Ingestion and Delivery
    widgets.push({
      type: 'metric',
      x: 0,
      y: 8,
      width: 6,
      height: 6,
      properties: {
        metrics: [
          ['AWS/Kinesis', 'IncomingRecords', 'StreamName', event.Kinesis.GameEventsStream, {id: 'records', color: '#2ca02c', label: 'Events Stream Incoming Records (Kinesis)'}],
          ['AWS/Firehose', 'DeliveryToS3.Records', 'DeliveryStreamName', event.Kinesis.GameEventsFirehose, {id: 'delivered', label: 'Firehose Records Delivered to S3', color: '#17becf'}],
          ['AWS/ApiGateway', 'Count', 'ApiName', event.GameAnalyticsApi.Name, 'Resource', '/applications/{applicationId}/events', 'Stage', event.GameAnalyticsApi.Stage, 'Method', 'POST', {label: 'Events REST API Request Count', color: '#1f77b4'}]
        ],
        view: 'timeSeries',
        stacked: false,
        region: this.config.region,
        title: 'Events Ingestion and Delivery',
        stat: 'Sum',
        yAxis: {
          left: {
            label: 'Count',
            showUnits: false
          }
        }
      }
    });

    // Events Processing Function Error and Success Rate
    widgets.push({
      type: 'metric',
      x: 6,
      y: 8,
      width: 6,
      height: 6,
      properties: {
        metrics: [
          ['AWS/Lambda','Errors', 'FunctionName', event.Functions.EventsProcessingFunction, 'Resource', event.Functions.EventsProcessingFunctionArn, {id: 'errors', stat: 'Sum', color: '#d13212', region: this.config.region}],
          ['AWS/Lambda', 'Invocations', 'FunctionName', event.Functions.EventsProcessingFunction, 'Resource', event.Functions.EventsProcessingFunctionArn, {id: 'invocations', stat: 'Sum', visible: false, region: this.config.region}],
          [{ expression: '100 - 100 * errors / MAX([errors, invocations])', label: 'Success rate (%)', id: 'availability', yAxis: 'right', region: this.config.region}]
        ],
        region: this.config.region,
        title: 'Lambda Error count and success rate (%)',
        period: 60,
        stat: 'Sum',
        yAxis: {
          right: {
            max: 100,
            label: 'Percent',
            showUnits: false
          },
          left: {
            showUnits: false,
            label: ''
          }
        },
        view: 'timeSeries',
        stacked: false
      }
    });

    // Events Processing Health
    widgets.push({
      type: 'metric',
      x: 0,
      y: 5,
      width: 12,
      height: 3,
      properties: {
        metrics: [
          ['AWS/Firehose', 'DeliveryToS3.DataFreshness', 'DeliveryStreamName', event.Kinesis.GameEventsFirehose, {visible: true, label: 'Data Freshness', period: 300, id: 'datafreshness', stat: 'Maximum'}],
          ['AWS/Lambda', 'Duration', 'FunctionName', event.Functions.EventsProcessingFunction, 'Resource', event.Functions.EventsProcessingFunctionArn, {id: 'duration', label: 'Lambda Duration', stat: 'Average', period: 300}],
          ['AWS/Lambda', 'ConcurrentExecutions', 'FunctionName', event.Functions.EventsProcessingFunction, {visible: true, label: 'Lambda Concurrency', id: 'concurrency', stat: 'Maximum', period: 300}],
          ['AWS/Lambda', 'Throttles', 'FunctionName', event.Functions.EventsProcessingFunction, {label: 'Lambda Throttles', id: 'throttles', visible: true, stat: 'Sum', period: 300}]
        ],
        view: 'singleValue',
        stacked: true,
        region: this.config.region,
        title: 'Events Processing Health',
        stat: 'Average'
      }
    });

    // Optionally create widgets for streaming analytics solution components if enabled
    if (event.StreamingAnalyticsEnabled === 'true') {
      // Streaming Analytics Header
      widgets.push({
        type: 'text',
        x: 12,
        y: 2,
        width: 12,
        height: 3,
        properties: {
          markdown: '\n## Real-time Streaming Analytics\nThe below metrics can be used to monitor the real-time streaming SQL analytics of events. Use the Kinesis Data Analytics MillisBehindLatest metric to help you track the lag on the Kinesis SQL Application from the latest events. The Analytics Processing function that processes KDA application outputs can be tracked to measure function concurrency, success percentage, processing duration and throttles.\n'
        }
      });

      // Streaming Analytics Function
      widgets.push({
        type: 'metric',
        properties: {
          metrics: [
            ['AWS/Lambda', 'ConcurrentExecutions', 'FunctionName', event.Functions.AnalyticsProcessingFunction, {label: 'Analytics Processing Concurrent Executions', stat: 'Maximum', id: 'concurrency'}],
            ['.', 'Duration', '.', '.', {label: 'Lambda Duration', id: 'duration', stat: 'Average'}],
            ['.', 'Throttles', '.', '.', {label: 'Lambda Throttles', id: 'throttles'}]
          ],
          view: 'singleValue',
          region: this.config.region,
          title: 'Real-time Analytics Health',
          stat: 'Sum',
          setPeriodToTimeRange: false
        },
        x: 12,
        y: 5,
        width: 12,
        height: 3
      });

      // Kinesis Analytics SQL Application
      widgets.push({
        type: 'metric',
        x: 12,
        y: 8,
        width: 6,
        height: 6,
        properties: {
          metrics: [
            ['AWS/KinesisAnalytics', 'MillisBehindLatest', 'Id', '1.1', 'Application', event.Kinesis.KinesisAnalyticsApp, 'Flow', 'Input']
          ],
          view: 'timeSeries',
          stacked: true,
          period: 60,
          region: this.config.region,
          stat: 'Average',
          title: 'Kinesis Analytics Latency'
        }
      });
        
      // Analytics Processing Function Error and Success Rate
      widgets.push({
        type: 'metric',
        x: 18,
        y: 8,
        width: 6,
        height: 6,
        properties: {
          metrics: [
            ['AWS/Lambda','Errors', 'FunctionName', event.Functions.AnalyticsProcessingFunction, 'Resource', event.Functions.AnalyticsProcessingFunctionArn, {id: 'errors', stat: 'Sum', color: '#d13212', region: this.config.region}],
            ['AWS/Lambda', 'Invocations', 'FunctionName', event.Functions.AnalyticsProcessingFunction, 'Resource', event.Functions.AnalyticsProcessingFunctionArn, {id: 'invocations', stat: 'Sum', visible: false, region: this.config.region}],
            [{ expression: '100 - 100 * errors / MAX([errors, invocations])', label: 'Success rate (%)', id: 'availability', yAxis: 'right', region: this.config.region}]
          ],
          region: this.config.region,
          title: 'Lambda Error count and success rate (%)',
          period: 60,
          stat: 'Sum',
          yAxis: {
            right: {
              max: 100,
              label: 'Percent',
              showUnits: false
            },
            left: {
              showUnits: false,
              label: ''
            }
          },
          view: 'timeSeries',
          stacked: false
        }
      });
    }
    console.log(`widgets: ${JSON.stringify(widgets)}`);
    let dashboard = {
      widgets: widgets
    };

    return new Promise((resolve, reject) => {
      const params = {
        DashboardName: event.DashboardName,
        DashboardBody: JSON.stringify(dashboard)
      };

      cloudwatch.putDashboard(params, function(err, data) {
        if (err) {
          console.log(JSON.stringify(err));
          reject(err);
        } else {
          console.log(data);
          resolve(data);
        }
      })
    });
  }
}

module.exports = cloudwatchHelper;
