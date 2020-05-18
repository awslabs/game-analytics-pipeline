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

console.log('Loading function');

const url = require('url');
const requestPromise = require('request-promise');
const moment = require('moment');
const DynamoDBHelper = require('./lib/dynamodb-helper.js');
const LambdaHelper = require('./lib/lambda-helper.js');
const S3Helper = require('./lib/s3-helper.js');
const AthenaHelper = require('./lib/athena-helper.js');
const GlueHelper = require('./lib/glue-helper.js');
const KinesisHelper = require('./lib/kinesis-helper.js');
const MetricsHelper = require('./lib/metrics-helper.js');
const { v4: uuidv4 } = require('uuid');
const crypto = require("crypto");

/**
 * Request handler.
 */
exports.handler = async (event, context, callback) => {
  console.log('Received event:', JSON.stringify(event, null, 2));

  let responseData = {};
  let responseStatus = 'FAILED';

  // Handling Promise Rejection
  process.on('unhandledRejection', error => {
    console.log(`Unhandled error: ${JSON.stringify(error)}`);
    throw error;
  });

  try {
    
    /**
     * Handle solution CloudFormation create events
     */
    if (event.RequestType === 'Create') {
      
      /**
       * Create solution UUID when the solution is created.
       */
      if (event.ResourceProperties.customAction === 'createUuid') {
        responseData = {
          UUID: uuidv4(),
        };
        responseStatus = 'SUCCESS';
        await sendResponse(event, callback, context.logStreamName, responseStatus, responseData);
      
      } else if (event.ResourceProperties.customAction === 'InvokeFunctionSync') {
        /**
         * Invokes a specified Lambda Function Synchronously. 
         * Used in the solution to trigger the GluePartitionCreator to create a new daily partition
         */
        let _lambdaHelper = new LambdaHelper();
        try {
          let functionArn = event.ResourceProperties.functionArn;
          responseData = await _lambdaHelper.invokeFunctionSync(functionArn);
          responseStatus = 'SUCCESS';
          await sendResponse(event, callback, context.logStreamName, responseStatus, responseData);
        } catch (err) {
          responseData = {
            Error: 'Error invoking Lambda Function'
          };
          responseStatus = 'FAILED';
          await sendResponse(event, callback, context.logStreamName, responseStatus, responseData);
        }
      } else if (event.ResourceProperties.customAction === 'uploadS3Object') {
        /**
         * Download artifact from AWS bucket and upload to solution bucket
         */
         let _s3Helper = new S3Helper();
         try {
           let sourceS3Bucket = event.ResourceProperties.sourceS3Bucket;
           let sourceS3Key = event.ResourceProperties.sourceS3Key;
           let destinationS3Bucket = event.ResourceProperties.destinationS3Bucket;
           let destinationS3Key = event.ResourceProperties.destinationS3Key;
           
           let object = await _s3Helper.getObject(sourceS3Bucket, sourceS3Key);
           await _s3Helper.uploadObject(destinationS3Bucket, destinationS3Key, object);
           responseData = {};
           responseStatus = 'SUCCESS';
           await sendResponse(event, callback, context.logStreamName, responseStatus, responseData);
         } catch (err) {
            console.log(`Error saving object to bucket`, JSON.stringify(err));
            responseData = {
              Error: 'Error saving object to S3 Bucket'
            };
            responseStatus = 'FAILED';
            await sendResponse(event, callback, context.logStreamName, responseStatus, responseData);
         }
      } else if (event.ResourceProperties.customAction === 'putDataCatalogEncryptionSettings') {
        /**
         * Enable data catalog encryption
         */
        let _glueHelper = new GlueHelper();
        try {
          let catalogId = event.ResourceProperties.catalogId;
          await _glueHelper.putDataCatalogEncryptionSettings(catalogId, 'SSE-KMS');
          responseData = {};
          responseStatus = 'SUCCESS';
          await sendResponse(event, callback, context.logStreamName, responseStatus, responseData);
        } catch (err) {
          console.log(`Error setting glue data catalog encryption settings`, JSON.stringify(err));
          responseData = {
            Error: 'Error setting glue data catalog encryption settings'
          };
          responseStatus = 'FAILED';
          await sendResponse(event, callback, context.logStreamName, responseStatus, responseData);
        }
      } else if (event.ResourceProperties.customAction === 'CreateApiAuthorization') {
        /**
         * Create an api key and generate authorization for default application
         */
        let _ddbHelper = new DynamoDBHelper();
        try {
          const application_id = event.ResourceProperties.application_id;
          const apiKeyId = uuidv4(); // generate a random identifier for the key
          const updated_at = moment().utc().format();
          const created_at = moment().utc().format();
          const ddbTable = event.ResourceProperties.authorizationsTable;
          
          let item = {
            api_key_value: crypto.randomBytes(64).toString('base64'), // generate random api key
            application_id: application_id,
            api_key_id: apiKeyId,
            api_key_name: event.ResourceProperties.key_name,
            api_key_description: event.ResourceProperties.key_description,
            updated_at: updated_at,
            created_at: created_at,
            enabled: true
          };
          await _ddbHelper.saveItem(item, ddbTable);
          responseData = {
            apiKeyId: apiKeyId 
          };
          responseStatus = 'SUCCESS';
          await sendResponse(event, callback, context.logStreamName, responseStatus, responseData);
        } catch (err) {
          responseData = {
            Error: 'Error registering api key with authorizations table'
          };
          responseStatus = 'FAILED';
          await sendResponse(event, callback, context.logStreamName, responseStatus, responseData);
        }
        
      } else if (event.ResourceProperties.customAction === 'sendAnonymousMetric') {
        responseStatus = 'SUCCESS';
        /**
         * Send annonymous metric.
         * Only when anonymous data is "Yes" to send when the solution is created
         */
        if (event.ResourceProperties.AnonymousData === 'Yes') {
          let _metric = {
            Solution: event.ResourceProperties.SolutionId,
            UUID: event.ResourceProperties.UUID,
            TimeStamp: moment().utc().format('YYYY-MM-DD HH:mm:ss.S'),
            Data: {
              Version: event.ResourceProperties.Version,
              Launch: moment().utc().format(),
              StreamingAnalyticsEnabled: event.ResourceProperties.EnableStreamingAnalytics,
              GameEventsStreamShardCount: event.ResourceProperties.GameEventsStreamShardCount,
              SolutionMode: event.ResourceProperties.SolutionMode
            }
          };
          
          let _metricsHelper = new MetricsHelper();
          try {
            await _metricsHelper.sendAnonymousMetric(_metric);
            responseData = {
              Message: 'Sent anonymous usage metrics.'
            };
          } catch (error) {
            // Throws error when sending anonymous launch metric fails.
            console.log('Sending anonymous launch metric failed and was skipped', error);
            responseData = {
              Error: 'Error sending anonymous metric, skipping'
            };
          }
        } else {
          console.log(`Anonymous usage metrics are disabled, skipping`);
        }
        await sendResponse(event, callback, context.logStreamName, responseStatus, responseData);
      } else if (event.ResourceProperties.customAction === 'createAthenaNamedQueries') {
          /**
           * Create default queries in Athena
           */
          let _athenaHelper = new AthenaHelper();
          const queries = [
            {
              "database": event.ResourceProperties.database,
              "name": "CreatePartitionedEventsJson",
              "description": "This command demonstrates how to create a new table of raw events transformed to JSON format. Output is partitioned by Application",
              "workgroup": event.ResourceProperties.workgroupName,
              "query": `CREATE TABLE events_json 
                WITH (
                     format = 'JSON',  
                     partitioned_by = ARRAY['application_id']) 
                AS SELECT year, month, day, event_id, application_id, event_type
                FROM "${event.ResourceProperties.database}"."${event.ResourceProperties.table}";`
            },
            {
              "database": event.ResourceProperties.database,
              "name": "DailyActiveUsersQuery",
              "description": "Daily active users",
              "workgroup": event.ResourceProperties.workgroupName,
              "query": `SELECT
                date(date_parse(CONCAT(year, '-', month, '-', day), '%Y-%m-%d')) as event_date,
                count(distinct user_id) as unique_users
                FROM "${event.ResourceProperties.database}"."${event.ResourceProperties.table}"
                WHERE event_type = 'login'
                GROUP BY date(date_parse(CONCAT(year, '-', month, '-', day), '%Y-%m-%d'))
                ORDER by event_date DESC;`
            },
            {
              "database": event.ResourceProperties.database,
              "name": "MonthlyActiveUsersQuery",
              "description": "Monthly active users",
              "workgroup": event.ResourceProperties.workgroupName,
              "query": `WITH detail AS (
                SELECT date_trunc('month', date(date_parse(CONCAT(year, '-', month, '-', day), '%Y-%m-%d'))) as event_month, *
                FROM "${event.ResourceProperties.database}"."${event.ResourceProperties.table}")
                SELECT
                event_month, COUNT(DISTINCT user_id) as unique_users
                FROM detail
                GROUP BY event_month;`
            },
            {
              "database": event.ResourceProperties.database,
              "name": "LatestEventsQuery",
              "description": "Get latest events by event_timestamp",
              "workgroup": event.ResourceProperties.workgroupName,
              "query": `SELECT *, from_unixtime(event_timestamp, 'America/New_York') as event_timestamp_america_new_york
                FROM "${event.ResourceProperties.database}"."${event.ResourceProperties.table}"
                ORDER BY event_timestamp_america_new_york DESC
                LIMIT 10;`
            },
            {
              "database": event.ResourceProperties.database,
              "name": "TotalEventsQuery",
              "description": "Total events",
              "workgroup": event.ResourceProperties.workgroupName,
              "query": `SELECT application_id, count(DISTINCT event_id) as event_count 
                FROM "${event.ResourceProperties.database}"."${event.ResourceProperties.table}"
                GROUP BY application_id`
            },
            {
              "database": event.ResourceProperties.database,
              "name": "TotalEventsMonthQuery",
              "description": "Total events over last month",
              "workgroup": event.ResourceProperties.workgroupName,
              "query": `WITH detail AS
                (SELECT date_trunc('month', date(date_parse(CONCAT(year, '-', month, '-', day), '%Y-%m-%d'))) as event_month, * 
                FROM "${event.ResourceProperties.database}"."${event.ResourceProperties.table}") 
                SELECT date_trunc('month', event_month) as month, application_id, count(DISTINCT event_id) as event_count 
                FROM detail 
                GROUP BY date_trunc('month', event_month), application_id`
            },
            {
              "database": event.ResourceProperties.database,
              "name": "TotalIapTransactionsLastMonth",
              "description": "Total IAP Transactions over the last month",
              "workgroup": event.ResourceProperties.workgroupName,
              "query": `WITH detail AS 
                (SELECT date_trunc('month', date(date_parse(CONCAT(year, '-', month, '-', day),'%Y-%m-%d'))) as event_month,* 
                FROM "${event.ResourceProperties.database}"."${event.ResourceProperties.table}") 
                SELECT date_trunc('month', event_month) as month, application_id, count(DISTINCT json_extract_scalar(event_data, '$.transaction_id')) as transaction_count 
                FROM detail WHERE json_extract_scalar(event_data, '$.transaction_id') is NOT null 
                AND event_type = 'iap_transaction'
                GROUP BY date_trunc('month', event_month), application_id`
            },
            {
              "database": event.ResourceProperties.database,
              "name": "AverageRevenuePerUser_USD",
              "description": "Average Revenue Per User (ARPU) US Dollars",
              "workgroup": event.ResourceProperties.workgroupName,
              "query": `SELECT
                date(date_parse(CONCAT(year, '-', month, '-', day), '%Y-%m-%d')) as event_date,
                SUM(CAST(json_extract_scalar(event_data, '$.currency_amount') as DOUBLE) * CAST(json_extract_scalar(event_data, '$.item_amount')as DOUBLE))/count(distinct user_id) as ARPU
                FROM "${event.ResourceProperties.database}"."${event.ResourceProperties.table}"
                WHERE json_extract_scalar(event_data, '$.currency_type') = 'USD'
                AND event_type = 'iap_transaction'
                GROUP BY date(date_parse(CONCAT(year, '-', month, '-', day), '%Y-%m-%d'))
                ORDER BY event_date DESC;`
            },
            {
              "database": event.ResourceProperties.database,
              "name": "AverageRevenuePerDAU_USD",
              "description": "Average Revenue Per DAU for US Dollar purchases",
              "workgroup": event.ResourceProperties.workgroupName,
              "query": `with arpu as
                (SELECT 
                date(date_parse(CONCAT(year, '-', month, '-', day), '%Y-%m-%d')) as event_date,
                SUM(CAST(json_extract_scalar(event_data, '$.currency_amount') as DOUBLE) * CAST(json_extract_scalar(event_data, '$.item_amount') as DOUBLE))/count(distinct user_id) as ARPU
                FROM "${event.ResourceProperties.database}"."${event.ResourceProperties.table}"
                WHERE json_extract_scalar(event_data, '$.currency_type') = 'USD' GROUP BY date(date_parse(CONCAT(year, '-', month, '-', day), '%Y-%m-%d'))
                AND event_type = 'iap_transaction'
                ORDER BY event_date DESC
                ), dau as
                (SELECT date(date_parse(CONCAT(year, '-', month, '-', day), '%Y-%m-%d')) as event_date,
                count(distinct user_id) as unique_users
                FROM "${event.ResourceProperties.database}"."${event.ResourceProperties.table}"
                GROUP BY date(date_parse(CONCAT(year, '-', month, '-', day), '%Y-%m-%d'))
                ORDER by event_date DESC
                )
                select arpu.event_date as event_date, cast(arpu.ARPU AS DOUBLE)/cast(dau.unique_users AS DOUBLE) as ARPDAU
                from
                arpu JOIN dau ON arpu.event_date = dau.event_date
                ORDER BY event_date DESC;`
            },
            {
              "database": event.ResourceProperties.database,
              "name": "NewUsersLastMonth",
              "description": "New Users over the last month",
              "workgroup": event.ResourceProperties.workgroupName,
              "query": `WITH detail AS (
                SELECT date_trunc('month', date(date_parse(CONCAT(year, '-', month, '-', day), '%Y-%m-%d'))) as event_month, *
                FROM "${event.ResourceProperties.database}"."${event.ResourceProperties.table}")
                SELECT
                date_trunc('month', event_month) as month,
                count(*) as new_accounts
                FROM detail
                WHERE event_type = 'user_registration'
                GROUP BY date_trunc('month', event_month);`
            },
            {
              "database": event.ResourceProperties.database,
              "name": "TotalUsersByCountry",
              "description": "Total users registered by country",
              "workgroup": event.ResourceProperties.workgroupName,
              "query": `SELECT
                json_extract_scalar(event_data, '$.country_id') as country,
                count(DISTINCT user_id) as unique_users
                FROM "${event.ResourceProperties.database}"."${event.ResourceProperties.table}"
                WHERE event_type = 'user_registration'
                GROUP BY json_extract_scalar(event_data, '$.country_id')`
            },
            {
              "database": event.ResourceProperties.database,
              "name": "TotalUsersByPlatform",
              "description": "Total users by platform",
              "workgroup": event.ResourceProperties.workgroupName,
              "query": `SELECT
                json_extract_scalar(event_data, '$.platform') as platforms,
                count(DISTINCT user_id) as unique_users
                FROM "${event.ResourceProperties.database}"."${event.ResourceProperties.table}"
                WHERE event_type = 'login'
                GROUP BY json_extract_scalar(event_data, '$.platform')`
            },
            {
              "database": event.ResourceProperties.database,
              "name": "TotalUsersByRank",
              "description": "Total users by Rank",
              "workgroup": event.ResourceProperties.workgroupName,
              "query": `SELECT
                json_extract_scalar(event_data, '$.user_rank_reached') as user_rank_reached,
                count(DISTINCT user_id) as unique_users
                FROM "${event.ResourceProperties.database}"."${event.ResourceProperties.table}"
                WHERE event_type = 'user_rank_up'
                GROUP BY json_extract_scalar(event_data, '$.user_rank_reached')
                ORDER BY json_extract_scalar(event_data, '$.user_rank_reached') DESC;`
            },
            {
              "database": event.ResourceProperties.database,
              "name": "TotalPlaysByLevel",
              "description": "Total number of times each level has been played",
              "workgroup": event.ResourceProperties.workgroupName,
              "query": `SELECT
                json_extract_scalar(event_data, '$.level_id') as level,
                count(json_extract_scalar(event_data, '$.level_id')) as number_of_plays
                FROM "${event.ResourceProperties.database}"."${event.ResourceProperties.table}"
                WHERE event_type = 'level_started'
                GROUP BY json_extract_scalar(event_data, '$.level_id')
                ORDER by json_extract_scalar(event_data, '$.level_id');`
            },
            {
              "database": event.ResourceProperties.database,
              "name": "TotalFailuresByLevel",
              "description": "Total number of failures on each level",
              "workgroup": event.ResourceProperties.workgroupName,
              "query": `SELECT
                json_extract_scalar(event_data, '$.level_id') as level,
                count(json_extract_scalar(event_data, '$.level_id')) as number_of_failures
                FROM "${event.ResourceProperties.database}"."${event.ResourceProperties.table}"
                WHERE event_type='level_failed'
                GROUP BY json_extract_scalar(event_data, '$.level_id')
                ORDER by json_extract_scalar(event_data, '$.level_id');`
            },
            {
              "database": event.ResourceProperties.database,
              "name": "TotalCompletionsByLevel",
              "description": "Total number of completions on each level",
              "workgroup": event.ResourceProperties.workgroupName,
              "query": `SELECT
                json_extract_scalar(event_data, '$.level_id') as level,
                count(json_extract_scalar(event_data, '$.level_id')) as number_of_completions
                FROM "<GameEventsDatabase>"."raw"
                WHERE event_type='level_completed'
                GROUP BY json_extract_scalar(event_data, '$.level_id')
                ORDER by json_extract_scalar(event_data, '$.level_id');`
            },
            {
              "database": event.ResourceProperties.database,
              "name": "LevelCompletionRate",
              "description": "Rate of completion for each level",
              "workgroup": event.ResourceProperties.workgroupName,
              "query": `with t1 as
                (SELECT json_extract_scalar(event_data, '$.level_id') as level, count(json_extract_scalar(event_data, '$.level_id')) as level_count 
                FROM "${event.ResourceProperties.database}"."${event.ResourceProperties.table}"
                WHERE event_type='level_started' GROUP BY json_extract_scalar(event_data, '$.level_id') 
                ),
                t2 as
                (SELECT json_extract_scalar(event_data, '$.level_id') as level, count(json_extract_scalar(event_data, '$.level_id')) as level_count 
                FROM "${event.ResourceProperties.database}"."${event.ResourceProperties.table}"
                WHERE event_type='level_completed'GROUP BY json_extract_scalar(event_data, '$.level_id') 
                )
                select t1.level, (cast(t1.level_count AS DOUBLE) / (cast(t2.level_count AS DOUBLE) + cast(t1.level_count AS DOUBLE))) * 100 as level_completion_rate from 
                t1 JOIN t2 ON t1.level = t2.level
                ORDER by level;`
            },
            {
              "database": event.ResourceProperties.database,
              "name": "AverageUserSentimentPerDay",
              "description": "User sentiment score by day",
              "workgroup": event.ResourceProperties.workgroupName,
              "query": `SELECT
                avg(CAST(json_extract_scalar(event_data, '$.user_rating') AS real)) AS average_user_rating, 
                date(date_parse(CONCAT(year, '-', month, '-', day), '%Y-%m-%d')) as event_date
                FROM "${event.ResourceProperties.database}"."${event.ResourceProperties.table}"
                WHERE json_extract_scalar(event_data, '$.user_rating') is not null
                GROUP BY date(date_parse(CONCAT(year, '-', month, '-', day), '%Y-%m-%d'));`
            },
            {
              "database": event.ResourceProperties.database,
              "name": "UserReportedReasonsCount",
              "description": "Reasons users are being reported, grouped by reason code",
              "workgroup": event.ResourceProperties.workgroupName,
              "query": `
                SELECT count(json_extract_scalar(event_data, '$.report_reason')) as count_of_reports, json_extract_scalar(event_data, '$.report_reason') as report_reason
                FROM "${event.ResourceProperties.database}"."${event.ResourceProperties.table}"
                GROUP BY json_extract_scalar(event_data, '$.report_reason')
                ORDER BY json_extract_scalar(event_data, '$.report_reason') DESC;`
            }
          ];
          try {
            console.log(`queries: ${JSON.stringify(queries)}`);
            for (const query of queries) {
              await _athenaHelper.createDefaultNamedQuery(query.database, query.name, query.workgroup, query.description, query.query);
            }
            responseData = {
              Message: 'Created queries'
            };
            responseStatus = 'SUCCESS';
            await sendResponse(event, callback, context.logStreamName, responseStatus, responseData);
          } catch (err) {
              responseData = {
                Error: 'Error creating athena queries'
              };
              responseStatus = 'FAILED';
              await sendResponse(event, callback, context.logStreamName, responseStatus, responseData);
          }
      } else if (event.ResourceProperties.customAction === 'saveDdbItem') {
        /**
         * Save DDB item
         */
        let _ddbHelper = new DynamoDBHelper();
        try {
          await _ddbHelper.saveItem(event.ResourceProperties.DdbItem, event.ResourceProperties.DdbTable);
          responseData = {
            Message: 'Saving item to DynamoDB table successful'
          };
          responseStatus = 'SUCCESS';
          await sendResponse(event, callback, context.logStreamName, responseStatus, responseData);
        } catch (error) {
          console.log(`Saving item to DyanmoDB table ${event.ResourceProperties.DdbTable} failed.`, error);
          responseData = {
            Error: 'Saving item to DynamoDB table failed'
          };
          responseStatus = 'FAILED';
          await sendResponse(event, callback, context.logStreamName, responseStatus, responseData);
        }
        
      } else if (event.ResourceProperties.customAction === 'createDefaultApplication') {
        /**
         * Create default application for solution
         */
        let _ddbHelper = new DynamoDBHelper();
        console.log(`Creating default application`);
        const application_id = uuidv4();
        let ddbTable = event.ResourceProperties.applicationsTable;
        try {
          let item = {
            application_id: application_id,
            application_name: event.ResourceProperties.application_name,
            updated_at: moment().utc().format(),
            created_at: moment().utc().format(),
            description: event.ResourceProperties.description
          };
          await _ddbHelper.saveItem(item, ddbTable);
          responseData = {
            application_name: item.application_name,
            application_id: item.application_id
          };
          responseStatus = 'SUCCESS';
          await sendResponse(event, callback, context.logStreamName, responseStatus, responseData);
        } catch (error) {
          console.log(`Creating default application failed.`, JSON.stringify(error));
          responseData = {
            Error: 'Failure saving item to DynamoDB table'
          };
          responseStatus = 'FAILED';
          await sendResponse(event, callback, context.logStreamName, responseStatus, responseData);
        }
      
      } else if (event.ResourceProperties.customAction === 'startKinesisAnalyticsApp') {
        /**
         * Start Kinesis Analytics application
         */
        let _kinesisHelper = new KinesisHelper();
        console.log(`Starting Kinesis Analytics application ${event.ResourceProperties.kinesisAnalyticsAppName}`);
        try {
          await _kinesisHelper.startKinesisAnalyticsApp(event.ResourceProperties.kinesisAnalyticsAppName);
          responseData = {
            Message: 'Started the Kinesis Analytics application'
          };
          responseStatus = 'SUCCESS';
          await sendResponse(event, callback, context.logStreamName, responseStatus, responseData);
        } catch (error) {
          console.log(`Failed to start the Kinesis Analytics application ${event.ResourceProperties.kinesisAnalyticsAppName}`, error);
          responseData = {
            Error: 'Failed to start the Kinesis Analytics app'
          };
          responseStatus = 'FAILED';
          await sendResponse(event, callback, context.logStreamName, responseStatus, responseData);
        }
      }
    } //end create
    
    
    /**
     * Handle solution CloudFormation create events
     */
    if (event.RequestType === 'Delete') {
      
      if (
        event.ResourceProperties.customAction === 'createUuid' 
        || event.ResourceProperties.customAction === 'startKinesisAnalyticsApp'
        || event.ResourceProperties.customAction === 'saveDdbItem'
        || event.ResourceProperties.customAction === 'createDefaultApplication'
        || event.ResourceProperties.customAction === 'CreateApiAuthorization'
        || event.ResourceProperties.customAction === 'InvokeFunctionSync'
        || event.ResourceProperties.customAction === 'putDataCatalogEncryptionSettings'
        || event.ResourceProperties.customAction === 'createAthenaNamedQueries'
        || event.ResourceProperties.customAction === 'uploadS3Object'
        ) {
          responseStatus = 'SUCCESS';
          await sendResponse(event, callback, context.logStreamName, responseStatus, responseData);
      }
      
      /**
       * Handle deletion for metrics
       */
      else if (event.ResourceProperties.customAction === 'sendAnonymousMetric') {
        responseStatus = 'SUCCESS';
        if (event.ResourceProperties.AnonymousData === 'Yes') { 
          let _metric = {
            Solution: event.ResourceProperties.SolutionId,
            UUID: event.ResourceProperties.UUID,
            TimeStamp: moment().utc().format('YYYY-MM-DD HH:mm:ss.S'),
            Data: {
              Version: event.ResourceProperties.Version,
              Deleted: moment().utc().format(),
              StreamingAnalyticsEnabled: event.ResourceProperties.EnableStreamingAnalytics,
              GameEventsStreamShardCount: event.ResourceProperties.GameEventsStreamShardCount,
              SolutionMode: event.ResourceProperties.SolutionMode
            }
          };
  
          let _metricsHelper = new MetricsHelper();
          try {
            await _metricsHelper.sendAnonymousMetric(_metric);
            responseData = {
              Message: 'Sending anonymous data successful.'
            };
          } catch (error) {
            console.log('Sending anonymous launch metric failed.', error);
            responseData = {
              Error: 'Sending anonymous launch metric failed.'
            };
          }
          await sendResponse(event, callback, context.logStreamName, responseStatus, responseData);
        }
      }
    }
    
    /**
     * Handle solution CloudFormation updates
     */
    if (event.RequestType === 'Update') {
      
      if ( event.ResourceProperties.customAction === 'createUuid' 
        || event.ResourceProperties.customAction === 'startKinesisAnalyticsApp'
        || event.ResourceProperties.customAction === 'saveDdbItem'
        || event.ResourceProperties.customAction === 'createDefaultApplication'
        || event.ResourceProperties.customAction === 'CreateApiAuthorization'
        || event.ResourceProperties.customAction === 'InvokeFunctionSync'
        || event.ResourceProperties.customAction === 'putDataCatalogEncryptionSettings'
        || event.ResourceProperties.customAction === 'createAthenaNamedQueries'
        || event.ResourceProperties.customAction === 'uploadS3Object'
      ) {
        responseStatus = 'SUCCESS';
        await sendResponse(event, callback, context.logStreamName, responseStatus, responseData);
      } 
      
      if (event.ResourceProperties.customAction === 'sendAnonymousMetric') {
        responseStatus = 'SUCCESS';
        /**
         * Send annonymous metric.
         * Only when anonymous data is "Yes" to send when the solution is created
         */
        if (event.ResourceProperties.AnonymousData === 'Yes') {
          let _metric = {
            Solution: event.ResourceProperties.SolutionId,
            UUID: event.ResourceProperties.UUID,
            TimeStamp: moment().utc().format('YYYY-MM-DD HH:mm:ss.S'),
            Data: {
              Version: event.ResourceProperties.Version,
              Updated: moment().utc().format(),
              StreamingAnalyticsEnabled: event.ResourceProperties.EnableStreamingAnalytics,
              GameEventsStreamShardCount: event.ResourceProperties.GameEventsStreamShardCount,
              SolutionMode: event.ResourceProperties.SolutionMode
            }
          };
  
          let _metricsHelper = new MetricsHelper();
          try {
            await _metricsHelper.sendAnonymousMetric(_metric);
            responseData = {
              Message: 'Sent anonymous usage metrics.'
            };
          } catch (error) {
            console.log('Sending anonymous launch metric failed and was skipped', error);
            responseData = {
              Error: 'Sending anonymous launch metric failed.'
            };
          }
        }
        await sendResponse(event, callback, context.logStreamName, responseStatus, responseData);
      }
    } 
  } catch (err) {
    console.log(`Error occurred while ${event.RequestType} ${event.ResourceType}:\n`, err);
    responseData = {
      Error: err.message,
    };
    responseStatus = 'FAILED';
    await sendResponse(event, callback, context.logStreamName, responseStatus, responseData);
  }
};

/**
 * Sends a response to the pre-signed S3 URL
 */
let sendResponse = async function (event, callback, logStreamName, responseStatus, responseData) {
  const responseBody = JSON.stringify({
    Status: responseStatus,
    Reason: `See the details in CloudWatch Log Stream: ${logStreamName}`,
    PhysicalResourceId: logStreamName,
    StackId: event.StackId,
    RequestId: event.RequestId,
    LogicalResourceId: event.LogicalResourceId,
    Data: responseData,
  });

  console.log('RESPONSE BODY:\n', responseBody);
  const parsedUrl = url.parse(event.ResponseURL);
  const options = {
    uri: `https://${parsedUrl.hostname}${parsedUrl.path}`,
    port: 443,
    method: 'PUT',
    headers: {
      'Content-Type': '',
      'Content-Length': responseBody.length,
    },
    body: responseBody,
  };

  try {
    await requestPromise(options);
    console.log('Successfully sent stack response!');
    callback(null, 'Successfully sent stack response!');
  } catch (error) {
    console.log('sendResponse Error:', error);
    callback(error);
  }
};
