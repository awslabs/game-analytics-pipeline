'use strict';

let lib = require('./lib/index.js');

exports.handler = function(event, context, callback) {
  console.log(`Events processing service received event`);

  lib
    .respond(event, context)
    .then(data => {
      return callback(null, data);
    })
    .catch(err => {
      return callback(err, null);
    });
};