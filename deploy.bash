PROJECT_NAME="geode-analytics"
VERSION="v1"

if [ -z $BRANCH_NAME ]; then
    # Jenkins runs script on git branch in a detached HEAD state.
    # Jenkins has BRANCH_NAME environment variable
    export BRANCH_NAME=`git rev-parse --abbrev-ref HEAD`
fi

# Check if we should deployed in China or World project
IS_CHINA=false
PROJECT_ENVIRONMENT="WORLD"
for arg in $@; do
    if [ $arg != "--china" ]; then
        echo "Exit : Unknown tag $arg"
        exit 1
    fi
    IS_CHINA=true
    PROJECT_ENVIRONMENT="CHINA"
done

echo "Game Analytics Pipeline will deployed in $PROJECT_ENVIRONMENT project !\n"

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

if $IS_CHINA; then
    export AWS_PROFILE=$AWS_PROFILE-china
    AWS_REGION="cn-north-1" # The region is the same in dev and prod environment
fi

DIST_OUTPUT_BUCKET="$PROJECT_NAME-output-bucket"
STACK_NAME="$PROJECT_NAME-$ENVIRONMENT"

# Run following command only the first time to create output bucket.
aws s3 mb s3://$DIST_OUTPUT_BUCKET-$AWS_REGION --region $AWS_REGION

cd ./deployment

# Build project (Templates + Lambdas)
./build-s3-dist.sh $DIST_OUTPUT_BUCKET analytics/$ENVIRONMENT $VERSION

# Store Global Assets to S3 (Templates)
aws s3 cp ./global-s3-assets s3://$DIST_OUTPUT_BUCKET-$AWS_REGION/analytics/$ENVIRONMENT/$VERSION --recursive --acl bucket-owner-full-control

# Store Regional Assets to S3 (Lambdas)
aws s3 cp ./regional-s3-assets s3://$DIST_OUTPUT_BUCKET-$AWS_REGION/analytics/$ENVIRONMENT/$VERSION --recursive --acl bucket-owner-full-control

# # Deploy Backoffce Remote Config API Gateway (Zappa)
# ./deploy-analytics-backoffice.sh $ENVIRONMENT $AWS_REGION $PROJECT_NAME

# Deploy CloudFormation by creating/updating Stack
aws cloudformation deploy \
    --template-file ./global-s3-assets/game-analytics-pipeline.template \
    --stack-name $STACK_NAME \
    --capabilities CAPABILITY_IAM \
    --s3-bucket $DIST_OUTPUT_BUCKET-$AWS_REGION \
    --s3-prefix templates \
    --capabilities CAPABILITY_NAMED_IAM \
    $PARAMETER_OVERRIDES
