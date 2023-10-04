if [ -z $BRANCH_NAME ]; then
    # Jenkins runs script on git branch in a detached HEAD state.
    # Jenkins has BRANCH_NAME environment variable
    export BRANCH_NAME=`git rev-parse --abbrev-ref HEAD`
fi

export AWS_PROFILE=dev
PARAMETER_OVERRIDES=""
if [ $BRANCH_NAME = "master" ]; then
    export AWS_PROFILE=prod
    AWS_REGION="us-east-1"
    ENVIRONMENT="prod"
    PARAMETER_OVERRIDES="--parameter-overrides KinesisStreamShards=5 SolutionMode=Prod"
elif [ $BRANCH_NAME = "dev" ]; then
    AWS_REGION="eu-west-3"
    ENVIRONMENT="dev"
else
    AWS_REGION="eu-west-3"
    ENVIRONMENT="sandbox"
fi

DIST_OUTPUT_BUCKET="analytics-output-bucket"
STACK_NAME="analytics-$ENVIRONMENT"
VERSION="v3"

# Run following commands only the first time to create bucket.
# aws s3 mb s3://$DIST_OUTPUT_BUCKET --region $AWS_REGION

cd ./deployment
chmod +x ./build-s3-dist.sh
chmod +x ./deploy-remote-config.sh

# Build project
./build-s3-dist.sh $DIST_OUTPUT_BUCKET analytics/$ENVIRONMENT $VERSION

# Store Regional Assets to S3
aws s3 cp ./regional-s3-assets s3://$DIST_OUTPUT_BUCKET-$AWS_REGION/analytics/$ENVIRONMENT/$VERSION --recursive --acl bucket-owner-full-control

# Store Global Assets to S3
aws s3 cp ./global-s3-assets s3://$DIST_OUTPUT_BUCKET-$AWS_REGION/analytics/$ENVIRONMENT/$VERSION --recursive --acl bucket-owner-full-control

# Deploy Remote Config API Gateway
./deploy-remote-config.sh $ENVIRONMENT $AWS_REGION

# Deploy CloudFormation by creating/updating Stack
aws cloudformation deploy \
    --template-file ./global-s3-assets/game-analytics-pipeline.template \
    --stack-name $STACK_NAME \
    --capabilities CAPABILITY_IAM \
    --s3-bucket $DIST_OUTPUT_BUCKET-$AWS_REGION \
    --s3-prefix templates \
    $PARAMETER_OVERRIDES
