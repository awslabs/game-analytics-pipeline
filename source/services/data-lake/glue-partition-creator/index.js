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

const AWS = require('aws-sdk')
const moment = require('moment');
const glue = new AWS.Glue({ apiVersion: '2017-03-31' });
global.StorageDescriptor = {};

exports.handler = async (event) => {
    var storageDescriptor = {};
    console.log(`Event: ${JSON.stringify(event)}`);
    const date = moment();
    const year = moment(date).format('YYYY');
    const month = moment(date).format('MM');
    const day = moment(date).format('DD');
    //const hour = moment(date).format('HH');
    console.log(`date: ${date}, year: ${year}, month: ${month}, day: ${day}`);
    
    try {
        let result = await glue.getPartition({
            DatabaseName: process.env.DATABASE_NAME,
            TableName: process.env.TABLE_NAME,
            PartitionValues: [String(year), String(month), String(day)]
        }).promise();
        console.log(`Partition already exists for year=${year}/month=${month}/day=${day}`);
        return result;
    } catch (err) {
        // If partition does not exist, create a new one based on the S3 key
        console.log(`Partition doesn't exist, retrieving table configuration from Glue`);
        let Table = await glue.getTable({
            DatabaseName: process.env.DATABASE_NAME,
            Name: process.env.TABLE_NAME,
        }).promise();
        console.log(`Table setting: ${JSON.stringify(Table)}`);
        storageDescriptor = Table.Table.StorageDescriptor;
        if(err.code === 'EntityNotFoundException'){
            let params = {
                DatabaseName: process.env.DATABASE_NAME,
                TableName: process.env.TABLE_NAME,
                PartitionInput: {
                    StorageDescriptor: {
                        ...storageDescriptor,
                        Location: `${storageDescriptor.Location}/year=${year}/month=${month}/day=${day}`
                    },
                    Values: [String(year), String(month), String(day)],
                }
            };
            await glue.createPartition(params).promise();
            console.log(`Created new table partition: ${storageDescriptor.Location}/year=${year}/month=${month}/day=${day}`);
        } else {
            console.log(`There was an error: ${JSON.stringify(err)}`);
            return err;
        }
    }
};