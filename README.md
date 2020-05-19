# AWS Game Analytics Pipeline Solution
Many Amazon Web Services (AWS) games customers want to build their own custom analytics solutions that provide flexibility and customization without the complexity of managing infrastructure. 

The [Game Analytics Pipeline](https://aws.amazon.com/solutions/game-analytics-pipeline/) Solution is a reference implementation of a serverless analytics pipeline that provides a solution for ingesting telemetry events from games and backend services. The solution addresses both real-time and batch analytics and integrates with AWS Glue and Amazon Simple Storage Service (Amazon S3) to provide data lake integration and cost effective storage.

## Getting Started

The solution source artifacts are provided in this repository to enable customization to the game analytics pipeline solution before deployment. To customize the solution source code and templates, an S3 Bucket is required to host assets used during the build and deployment process.

The build script provided with the solution can be run manually from a command line or can be executed within an automated build/release pipeline. The build script has been tested on Amazon Linux 2 platform. [AWS CodeBuild](https://aws.amazon.com/codebuild/) can be used to automated the build process and provides a variety of custom build environments, including Amazon Linux 2.

#### 1. Prerequisites
The following procedures assumes that all of the OS-level configuration has been completed. They are:

* [AWS Command Line Interface](https://aws.amazon.com/cli/)
* Node.js 12.x
* Python 3

The game analytics pipeline solution is developed with Node.js for the backend services that run in AWS Lambda. The latest version of the game analytics pipeline solution has been tested with Node.js v12.x. The solution also includes a demo script for generating sample game events, which is developed in Python and tested with Python 3.x. 

> Note: Python is not required to be installed on the system unless the sample events generator Python script is used. Additional prerequisites may be required if customization includes changing the solution code to use another runtime within AWS Lambda.
  
#### 2. Clone the game analytics pipeline solution

```
git clone https://github.com/awslabs/game-analytics-pipeline.git
```

> The build process requires the use of an Amazon S3 Bucket to store packaged artifacts. The build script packages the AWS Lambda Functions into zip files and stores them in the S3 Bucket for reference by the CloudFormation template during deployment. The S3 Bucket must exist in the same AWS Region where the CloudFormation template will be deployed. 
	
#### 3. Configure environment:
The solution build script requires environment variables to be configured prior to building the solution Configure the below environment variables:

```
export AWS_REGION=<AWS Region code>
export VERSION=<version>
export SOLUTION_NAME=<Provide a name solution name>   
export DIST_OUTPUT_BUCKET=<A name used for the S3 Bucket>
```

#### 4. Create an S3 Bucket for storing build artifacts in a supported AWS Region:

Create an S3 bucket with the region code appended to the name of the bucket, so that AWS CloudFormation can reference regionally hosted assets.

```
aws s3 mb s3://$DIST_OUTPUT_BUCKET-$AWS_REGION --region $AWS_REGION
```

> Note: In order to simplify the solution deployment, the build script automatically builds and re-packages each AWS Lambda Function during each build script execution. The script can be modified to support custom build and deployment requirements and the environment variables can be configured automatically in build tools, including AWS CodeBuild.

#### 5. Build the game analytics pipeline solution for deployment:
Make any modifications or customizations to the solution source code and template, and then use the below commands to build the solution:


``` 
cd ./deployment
```

```
chmod +x ./build-s3-dist.sh
./build-s3-dist.sh $DIST_OUTPUT_BUCKET $SOLUTION_NAME $VERSION
``` 

#### 6. Upload deployment assets to your Amazon S3 bucket:

```
aws s3 cp ./global-s3-assets s3://$DIST_OUTPUT_BUCKET-$AWS_REGION/$SOLUTION_NAME/$VERSION --recursive --acl bucket-owner-full-control
aws s3 cp ./regional-s3-assets s3://$DIST_OUTPUT_BUCKET-$AWS_REGION/$SOLUTION_NAME/$VERSION --recursive --acl bucket-owner-full-control
```

#### 7. Deploy the game analytics pipeline solution:
Deploy the solution CloudFormation template using the local packaged template or by referencing the uploaded template stored in Amazon S3:

```
aws cloudformation deploy --template-file ./global-s3-assets/game-analytics-pipeline.template --stack-name <STACK_NAME> --capabilities CAPABILITY_IAM  --s3-bucket $DIST_OUTPUT_BUCKET-$AWS_REGION
```

> Include optional parameters as needed, for example to receive SNS notifications from solution alarms, use ```--parameter-overrides SolutionAdminEmailAddress=<EMAIL_ADDRESS>```. A confirmation email is sent to the email address to verify subscription to the SNS Topic.


## File Structure 
 
``` 
|-deployment/ 
  |-build-s3-dist.sh  [ shell script for packaging distribution assets ] 
  |-game-analytics-pipeline.template  [ CloudFormation deployment template ] 
|-source/ 
  |-services/
    |-events_processing/ [ source code for lambda function that processes ingested events ]
  	|-analytics_processing/ [ Lambda function for processing output from Kinesis Data Analytics application]
  	|-api
  	  |-admin  [ API Microservice used to register new applications and authorizations for sending analytics events]
  	  |-lambda_authorizer  [ API Gateway Lambda Authorizer function used to authorize requests to /events endpoint]
  	|-data_lake  
   	  |-etl_processing/  [  contains PySpark source code for solution ETL Job ]
   	  |-glue_partition_creator/ [ source code for function that creates glue table partitions ]
|-demo/ [ contains the demo Python script for testing the solution with sample datasets]
|-resources/
  |-helper/ [ contains the Lambda custom resource helper function code] 
  |-usage-metrics/	[ source code for generating anonymous usage data]
  |-game-analytics-pipeline_postman_collection.json. [Postman collection file that is provided to help configure Postman for use with the solution]
  	 
``` 

Each Lambda Function follows the structure of:

```
|-service-name/
  |-lib/
    |-[service module libraries and other function artifacts]
  |-index.js [injection point for Lambda handler]
  |-package.json
``` 
*** 
 
 
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: MIT-0