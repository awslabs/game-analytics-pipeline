AWS_REGION="eu-west-3"
STACK_NAME="analytics-dev"
DIST_OUTPUT_BUCKET="$STACK_NAME-output-bucket"
VERSION="v1"

# Run following commands only the first time to create bucket.
# aws s3 mb s3://$DIST_OUTPUT_BUCKET-$AWS_REGION --region $AWS_REGION

cd ./deployment
chmod +x ./build-s3-dist.sh

# Build project
./build-s3-dist.sh $DIST_OUTPUT_BUCKET $STACK_NAME $VERSION

# Store Regional Assets to S3
aws s3 cp ./regional-s3-assets s3://$DIST_OUTPUT_BUCKET-$AWS_REGION/$STACK_NAME/$VERSION --recursive --acl bucket-owner-full-control

# Store Global Assets to S3
aws s3 cp ./global-s3-assets s3://$DIST_OUTPUT_BUCKET-$AWS_REGION/$STACK_NAME/$VERSION --recursive --acl bucket-owner-full-control

# Deploy CloudFormation by creating/updating Stack
aws cloudformation deploy --template-file ./global-s3-assets/game-analytics-pipeline.template --stack-name $STACK_NAME --capabilities CAPABILITY_IAM  --s3-bucket $DIST_OUTPUT_BUCKET-$AWS_REGION
