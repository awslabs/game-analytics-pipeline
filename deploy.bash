export AWS_REGION="eu-west-3"
export VERSION="test-version"
export SOLUTION_NAME="test-solution"
export DIST_OUTPUT_BUCKET="test-dist-output-bucket"

# Run following commands only the first time to create bucket.
# aws s3 mb s3://$DIST_OUTPUT_BUCKET-$AWS_REGION --region $AWS_REGION
# put-bucket-versioning --bucket $DIST_OUTPUT_BUCKET-$AWS_REGION --versioning-configuration Status=Enabled

cd ./deployment
chmod +x ./build-s3-dist.sh

# Build project
./build-s3-dist.sh $DIST_OUTPUT_BUCKET $SOLUTION_NAME $VERSION

# Store Regional Assets to S3
aws s3 cp ./regional-s3-assets s3://$DIST_OUTPUT_BUCKET-$AWS_REGION/$SOLUTION_NAME/$VERSION --recursive --acl bucket-owner-full-control

# Rertieve Object Versions of Regional Assets
EVENTS_PROCESSING_ZIP_VERSION=$(aws s3api head-object --bucket "$DIST_OUTPUT_BUCKET-$AWS_REGION" --key "$SOLUTION_NAME/$VERSION/events-processing.zip" --query 'VersionId' --output text)
sed -i -e s/%%EVENTS_PROCESSING_ZIP_VERSION%%/$EVENTS_PROCESSING_ZIP_VERSION/g global-s3-assets/*.template

ANALYTICS_PROCESSING_ZIP_VERSION=$(aws s3api head-object --bucket "$DIST_OUTPUT_BUCKET-$AWS_REGION" --key "$SOLUTION_NAME/$VERSION/analytics-processing.zip" --query 'VersionId' --output text)
sed -i -e s/%%ANALYTICS_PROCESSING_ZIP_VERSION%%/$ANALYTICS_PROCESSING_ZIP_VERSION/g global-s3-assets/*.template

ADMIN_ZIP_VERSION=$(aws s3api head-object --bucket "$DIST_OUTPUT_BUCKET-$AWS_REGION" --key "$SOLUTION_NAME/$VERSION/admin.zip" --query 'VersionId' --output text)
sed -i -e s/%%ADMIN_ZIP_VERSION%%/$ADMIN_ZIP_VERSION/g global-s3-assets/*.template

LAMBDA_AUTHORIZER_ZIP_VERSION=$(aws s3api head-object --bucket "$DIST_OUTPUT_BUCKET-$AWS_REGION" --key "$SOLUTION_NAME/$VERSION/lambda-authorizer.zip" --query 'VersionId' --output text)
sed -i -e s/%%LAMBDA_AUTHORIZER_ZIP_VERSION%%/$LAMBDA_AUTHORIZER_ZIP_VERSION/g global-s3-assets/*.template

GLUE_PARTITION_CREATOR_ZIP_VERSION=$(aws s3api head-object --bucket "$DIST_OUTPUT_BUCKET-$AWS_REGION" --key "$SOLUTION_NAME/$VERSION/glue-partition-creator.zip" --query 'VersionId' --output text)
sed -i -e s/%%GLUE_PARTITION_CREATOR_ZIP_VERSION%%/$GLUE_PARTITION_CREATOR_ZIP_VERSION/g global-s3-assets/*.template

SOLUTION_HELPER_ZIP_VERSION=$(aws s3api head-object --bucket "$DIST_OUTPUT_BUCKET-$AWS_REGION" --key "$SOLUTION_NAME/$VERSION/solution-helper.zip" --query 'VersionId' --output text)
sed -i -e s/%%SOLUTION_HELPER_ZIP_VERSION%%/$SOLUTION_HELPER_ZIP_VERSION/g global-s3-assets/*.template

# Store Global Assets to S3
aws s3 cp ./global-s3-assets s3://$DIST_OUTPUT_BUCKET-$AWS_REGION/$SOLUTION_NAME/$VERSION --recursive --acl bucket-owner-full-control

# Deploy CloudFormation by creating/updating Stack
aws cloudformation deploy --template-file ./global-s3-assets/game-analytics-pipeline.template --stack-name test-stack-name --capabilities CAPABILITY_IAM  --s3-bucket $DIST_OUTPUT_BUCKET-$AWS_REGION
