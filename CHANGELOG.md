# Change Log
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] - 2020-08-31
### Updated
- Updated CloudFormation template to move CloudWatch Dashboard body out of the YAML template and into a new custom resource library ```cloudwatch-helper.js```. This code conditionally creates the streaming analytics dashboard widgets only if streaming analytics is enabled as a CloudFormation parameter which fixes a previous bug that wasn't handling this properly. This should also make it easier to customize widget creation.
- Minor improvements to README for typos and further clarifications
- Update CloudFormation with additional conditional logic to some of the resources that should only be launched if streaming analytics is enabled.
- Updated event schema used in the solution to include ```app_version``` as a new top-level field.
- Updates to Athena and Kinesis Data Analytics queries
- Error handling improvements, bug fixes

### Removed
- Remove ```client_id```,  ```user_id```, and ```session_id``` fields from the solution. These are removed to enable privacy-friendly data collection use cases by default by removing the ability to attribute events to a specific user or device/client. If these fields are required, the event schema can be customized to include this before deployment.


## [1.0.0] - 2020-05-20
### Added
- initial repository version
