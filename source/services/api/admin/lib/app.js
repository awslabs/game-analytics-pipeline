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
const Application = require('./admin.js');
const express = require('express');
const bodyParser = require('body-parser');
const cors = require('cors');
const awsServerlessExpressMiddleware = require('aws-serverless-express/middleware');
const app = express();
const router = express.Router();

// declare a new express app
router.use(cors());
router.use((req, res, next) => {
  bodyParser.json()(req, res, err => {
    if (err) {
      return res.status(400).json({
        'error': 'BadRequest',
        'error_detail': err.message
      });
    }
    next();
  });
});
router.use(bodyParser.urlencoded({extended: true}));
router.use(awsServerlessExpressMiddleware.eventContext());

// List applications
const listApplications = async (req, res) => {
  console.log(`Attempting to retrieve registered applications`);
  let _application = new Application();
  try {
    const result = await _application.listApplications();
    res.json(result);
  } catch (err) {
    console.log(JSON.stringify(err));
    return res.status(err.code).json({
      'error': err.error,
      'error_detail': err.message
    });
  }
};


// Get detail for an application
const getApplicationDetail = async (req, res) => {
  console.log(`Attempting to retrieve application detail information.`);
  const applicationId = req.params.applicationId;
  let _application = new Application();
  try {
    const result = await _application.getApplicationDetail(applicationId);
    res.json(result);
  } catch (err) {
    console.log(JSON.stringify(err));
    return res.status(err.code).json({
      'error': err.error,
      'error_detail': err.message
    });
  }
};

// Creates a new application
const createApplication = async (req, res) => {
  console.log(`Attempting to create new registered application`);
  const body = req.body;
  let _application = new Application();
  try {
    if (!body.Name || typeof body.Name !== "string") {
      console.log(`An application name must be provided`);
      return res.status(400).json({
        'error': 'InvalidParameterException',
        'error_detail': 'Name is required and must be string'
      });
    }
    if (body.Description && typeof body.Description !== "string") {
      console.log(`Description must be a string value`);
      return res.status(400).json({
        'error': 'InvalidParameterException',
        'error_detail': 'Description must be string'
      });
    }
    const result = await _application.createApplication(body);
    res.json(result);
  } catch (err) {
    console.log(JSON.stringify(err));
    return res.status(err.code).json({
      'error': err.error,
      'error_detail': err.message
    });
  }
};


// Deletes a registered application
const deleteApplication = async (req, res) => {
  console.log(`Attempting to delete registered application`);
  const applicationId = req.params.applicationId;
  let _application = new Application();
  try {
    const result = await _application.deleteApplication(applicationId);
    res.json(result);
  } catch (err) {
    console.log(JSON.stringify(err));
    return res.status(err.code).json({
      'error': err.error,
      'error_detail': err.message
    });
  }
};

// Creates events api authorization
const createAuthorization = async (req, res) => {
  console.log(`Attempting to create authorization`);
  let _application = new Application();
  try {
    const body = req.body;
    const apiKeyName = body.Name;
    const apiKeyDescription = body.Description;
    const applicationId = req.params.applicationId;
    if (!apiKeyName || typeof apiKeyName !== "string") {
      console.log(`A name must be provided`);
      return res.status(400).json({
        'error': 'InvalidParameterException',
        'error_detail': 'Name is required and must be string'
      });
    }
    if (apiKeyDescription && typeof apiKeyDescription !== "string") {
      console.log(`Description must be a string value`);
      return res.status(400).json({
        'error': 'InvalidParameterException',
        'error_detail': 'Description must be string'
      });
    }
    
    // First check that provided application is valid
    await _application.getApplicationDetail(applicationId);
    const apiKey = await _application.createApiKey(apiKeyName, apiKeyDescription);
    const result = await _application.createAuthorization(apiKey.value, applicationId, apiKeyName, apiKeyDescription, apiKey.id);
    res.json(result);
  } catch (err) {
    console.log(JSON.stringify(err));
    return res.status(err.code).json({
      'error': err.error,
      'error_detail': err.message
    });
  }
};

// Delete authorization
const deleteAuthorization = async (req, res) => {
  console.log(`Attempting to delete authorization`);
  const applicationId = req.params.applicationId;
  const apiKeyId = req.params.apiKeyId;
  let _application = new Application();
  try {
    const result = await _application.deleteAuthorization(apiKeyId, applicationId);
    res.json(result);
  } catch (err) {
    console.log(JSON.stringify(err));
    return res.status(err.code).json({
      'error': err.error,
      'error_detail': err.message
    });
  }
};

// Modify authorization. 
const modifyAuthorization = async (req, res) => {
  console.log(`Attempting to modify authorization`);
  const applicationId = req.params.applicationId;
  const apiKeyId = req.params.apiKeyId;
  const body = req.body;
  let _application = new Application();
  try {
    const enabled = body.Enabled;
    if (typeof enabled === "boolean") {
      const result = await _application.modifyAuthorization(apiKeyId, applicationId, enabled);
      res.json(result);
    } else {
      console.log(`Enabled is required and must be of type boolean`);
      return res.status(400).json({
        'error': 'InvalidParameterException',
        'error_detail': 'Enabled field is required and must be boolean value'
      });
    }
  } catch (err) {
    console.log(JSON.stringify(err));
    return res.status(err.code).json({
      'error': err.error,
      'error_detail': err.message
    });
  }
};

// List authorizations for an application
const listAuthorizations = async (req, res) => {
  console.log(`Attempting to list authorizations`);
  const applicationId = req.params.applicationId;
  let _application = new Application();
  try {
    const result = await _application.listApplicationAuthorizations(applicationId);
    res.json(result);
  } catch (err) {
    console.log(JSON.stringify(err));
    return res.status(err.code).json({
      'error': err.error,
      'error_detail': err.message
    });
  }
}; 

// Get detail for an authorization
const getAuthorizationDetail = async (req, res) => {
  console.log(`Attempting to retrieve authorization detail information.`);
  const applicationId = req.params.applicationId;
  const apiKeyId = req.params.apiKeyId;
  let _application = new Application();
  try {
    const result = await _application.getAuthorizationDetail(apiKeyId, applicationId);
    res.json(result);
  } catch (err) {
    console.log(JSON.stringify(err));
    return res.status(err.code).json({
      'error': err.error,
      'error_detail': err.message
    });
  }
};

/****************************
 * Event methods *
****************************/


router.get('/applications', listApplications);
router.post('/applications', createApplication);

router.get('/applications/:applicationId', getApplicationDetail);
router.delete('/applications/:applicationId', deleteApplication);

router.post('/applications/:applicationId/authorizations', createAuthorization);
router.get('/applications/:applicationId/authorizations', listAuthorizations);
router.get('/applications/:applicationId/authorizations/:apiKeyId', getAuthorizationDetail);
router.put('/applications/:applicationId/authorizations/:apiKeyId', modifyAuthorization);
router.delete('/applications/:applicationId/authorizations', deleteAuthorization);
router.delete('/applications/:applicationId/authorizations/:apiKeyId', deleteAuthorization);
//router.put('/registrations/:registration_name', updateRegistration);

app.use('/', router);

// Export the app object. When executing the application local this does nothing. However,
// to port it to AWS Lambda we will create a wrapper around that will load the app from
// this file
module.exports = app;
