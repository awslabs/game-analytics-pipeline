if [ -z $BRANCH_NAME ]; then
    # Jenkins runs script on git branch in a detached HEAD state.
    # Jenkins has BRANCH_NAME environment variable
    export BRANCH_NAME=`git rev-parse --abbrev-ref HEAD`
fi

if [ $BRANCH_NAME = "master" ]; then
    AWS_REGION="us-east-1"
    STACK_NAME="analytics-prod"
elif [ $BRANCH_NAME = "dev" ]; then
    AWS_REGION="eu-west-3"
    STACK_NAME="analytics-dev"
else
    AWS_REGION="eu-west-3"
    STACK_NAME="analytics-branch"
fi

DIST_OUTPUT_BUCKET="analytics-output-bucket"
VERSION="v1"

# Run following commands only the first time to create bucket.
# aws s3 mb s3://$DIST_OUTPUT_BUCKET --region $AWS_REGION

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
