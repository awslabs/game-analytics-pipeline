'use strict';

const AWS = require('aws-sdk');
const NodeCache = require('node-cache');

/**
 * Applications table results cache
 * Maintains a local cache of registered Applications in DynamoDB. 
 */
global.abtestsCache = new NodeCache({ stdTTL: process.env.CACHE_TIMEOUT_SECONDS, checkPeriod: 60, maxKeys: 1000, useClones: false });

const respond = async (event, context) => {
  console.log(`Attempting to retrieve remote configs.`);
  console.log(`Event : ${JSON.stringify(event)}`);
  console.log(`Context : ${JSON.stringify(context)}`);

  const { userId } = event;

  const remoteConfigs = {}
  const docClient = new AWS.DynamoDB.DocumentClient({
    credentials: new AWS.EnvironmentCredentials('AWS'), // Lambda provided credentials,
    region: process.env.AWS_REGION,
  });


  const remoteConfigsParams = {
    TableName: process.env.REMOTE_CONFIGS_TABLE,
    IndexName: 'active-index',
    KeyConditionExpression: 'active = :active',
    ExpressionAttributeValues: {
      ':active': 1
    }
  }
  const remoteConfigsResult = await docClient.query(remoteConfigsParams).promise()

  await Promise.all(remoteConfigsResult.Items.map(async function (remoteConfig) {
    let value = remoteConfig.reference_value;
    let valueOrigin = "reference_value";

    let abtestsResult = global.abtestsCache.get(remoteConfig.ID);
    if (abtestsResult === undefined) {
      const abtestsParams = {
        TableName: process.env.ABTESTS_TABLE,
        IndexName: 'active-index',
        KeyConditionExpression: 'active = :active',
        FilterExpression: 'remote_config_ID = :remote_config_ID and paused = :paused',
        ExpressionAttributeValues: {
          ':active': 1,
          ':remote_config_ID': remoteConfig.ID,
          ':paused': false
        },
      }
      abtestsResult = await docClient.query(abtestsParams).promise()
      global.abtestsCache.set(remoteConfig.ID, remoteConfigsResult);
    }
    const [abtest = undefined] = abtestsResult.Items;

    if (abtest) {
      const usersAbtestsParams = {
        TableName: process.env.USERS_ABTESTS_TABLE,
        Key: { "uid": userId, "abtest_ID": abtest.ID }
      }
      const usersAbtestsResult = await docClient.get(usersAbtestsParams).promise()
      if (!usersAbtestsResult.Item) {
        const isInTest = Math.floor(Math.random() * 100) < abtest.target_user_percent
        valueOrigin = isInTest ? "abtest" : "reference_value"
        if (isInTest) {
          const choices = [remoteConfig.reference_value, ...abtest.variants]
          value = choices[Math.floor(Math.random() * choices.length)]
        }
        const putUsersAbtestsParams = {
          TableName: process.env.USERS_ABTESTS_TABLE,
          Item: {
            "uid": userId,
            "abtest_ID": abtest.ID,
            "is_in_test": isInTest,
            "value": value,
          }
        }
        await docClient.put(putUsersAbtestsParams).promise()
      } else {
        value = usersAbtestsResult.Item.value
        valueOrigin = usersAbtestsResult.Item.is_in_test ? "abtest" : "reference_value"
      }
    }

    remoteConfigs[remoteConfig.name] = {
      "value": value,
      "value_origin": valueOrigin,
    };
  }));

  return Promise.resolve(remoteConfigs);
};

module.exports = {
  respond
};
