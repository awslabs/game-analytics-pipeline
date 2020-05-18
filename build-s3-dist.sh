#!/bin/bash  
#  
# This assumes all of the OS-level configuration has been completed and git repo has already been cloned  
#  
# This script should be run from the repo's deployment directory  
# cd deployment  
# ./build-s3-dist.sh source-bucket-base-name trademarked-solution-name version-code  
#  
# Paramenters:  
#  - source-bucket-base-name: Name for the S3 bucket location where the template will source the Lambda  
#    code from. The template will append '-[region_name]' to this bucket name.  
#    For example: ./build-s3-dist.sh solutions my-solution v1.0.0  
#    The template will then expect the source code to be located in the solutions-[region_name] bucket  
#  
#  - trademarked-solution-name: name of the solution for consistency  
#  
#  - version-code: version of the package  
  
# Check to see if input has been provided:  
if [ -z "$1" ] || [ -z "$2" ] || [ -z "$3" ]; then  
    echo "Please provide the base source bucket name, trademark approved solution name and version where the lambda code will eventually reside."  
    echo "For example: ./build-s3-dist.sh solutions trademarked-solution-name v1.0.0"  
    exit 1  
fi  
bucket=$1
tmsn=$2
version=$3

do_cmd () {
	echo "------ EXEC $*"
	$*
}
do_replace() {
	replace="s/$2/$3/g"
	file=$1
	do_cmd sed -i $replace $file
}
# On entry it is expected that we are in the deployment folder of the build
 
# Get reference for all important folders  
template_dir="$PWD"
template_dist_dir="$template_dir/global-s3-assets"
build_dist_dir="$template_dir/regional-s3-assets"
source_dir="$template_dir/../source"

echo "------------------------------------------------------------------------------"  
echo "[Init] Clean old dist folders"  
echo "------------------------------------------------------------------------------"  
do_cmd rm -rf $template_dist_dir  
do_cmd mkdir -p $template_dist_dir  
do_cmd rm -rf $build_dist_dir  
do_cmd mkdir -p $build_dist_dir  
do_cmd rm -rf $template_dir/dist
do_cmd mkdir -p $template_dir/dist

echo "------------------------------------------------------------------------------" 
echo "Packaging templates" 
echo "------------------------------------------------------------------------------" 
do_cmd cp $template_dir/game-analytics-pipeline.yaml $template_dir/dist/

echo "------------------------------------------------------------------------------" 
echo "Updating Bucket name"
echo "------------------------------------------------------------------------------" 
for file in $template_dir/dist/*.yaml
do
	do_replace $file '%%BUCKET_NAME%%' $bucket
done


echo "------------------------------------------------------------------------------" 
echo "Updating Solution name"
echo "------------------------------------------------------------------------------" 
for file in $template_dir/dist/*.yaml
do
	do_replace $file '%%SOLUTION_NAME%%' $tmsn
done


echo "------------------------------------------------------------------------------" 
echo "Updating version name"
echo "------------------------------------------------------------------------------" 
for file in $template_dir/dist/*.yaml
do
	do_replace $file '%%VERSION%%' $version
done

echo "------------------------------------------------------------------------------"
echo "Packaging Lambda Function - Analytics Processing"
echo "------------------------------------------------------------------------------"
do_cmd cd $source_dir/services/analytics-processing
do_cmd npm run build
do_cmd cp dist/analytics-processing.zip $build_dist_dir/analytics-processing.zip

echo "------------------------------------------------------------------------------"  
echo "Packaging Lambda Function - Events Processing"  
echo "------------------------------------------------------------------------------"  
do_cmd cd $source_dir/services/events-processing
do_cmd npm run build
do_cmd cp dist/events-processing.zip $build_dist_dir/events-processing.zip

echo "------------------------------------------------------------------------------"  
echo "Packaging Lambda Function - Applications admin service"  
echo "------------------------------------------------------------------------------"  
do_cmd cd $source_dir/services/api/admin
do_cmd npm run build
do_cmd cp dist/admin.zip $build_dist_dir/admin.zip


echo "------------------------------------------------------------------------------"  
echo "Packaging Lambda Function - Lambda Authorizer"  
echo "------------------------------------------------------------------------------"  
do_cmd cd $source_dir/services/api/lambda-authorizer
do_cmd npm run build
do_cmd cp dist/lambda-authorizer.zip $build_dist_dir/lambda-authorizer.zip

echo "------------------------------------------------------------------------------"  
echo "Packaging Lambda Function - Glue Partition Creator"  
echo "------------------------------------------------------------------------------"  
do_cmd cd $source_dir/services/data-lake/glue-partition-creator
do_cmd npm run build
do_cmd cp dist/glue-partition-creator.zip $build_dist_dir/glue-partition-creator.zip

echo "------------------------------------------------------------------------------"
echo "Packaging Lambda Function - Solution Helper"
echo "------------------------------------------------------------------------------"
do_cmd cd $source_dir/resources/solution-helper
do_cmd npm run build
do_cmd cp ./dist/solution-helper.zip $build_dist_dir/solution-helper.zip

echo "------------------------------------------------------------------------------"
echo "Copying Glue ETL Code to regional assets folder"
echo "------------------------------------------------------------------------------"
do_cmd cd $source_dir/services/data-lake/glue-scripts
do_cmd cp game_events_etl.py $build_dist_dir/game_events_etl.py

echo "------------------------------------------------------------------------------"
echo "Package AWS SAM template into CloudFormation"
echo "------------------------------------------------------------------------------"
do_cmd cd $template_dir/dist
do_cmd aws cloudformation package --template-file ./game-analytics-pipeline.yaml --s3-bucket $bucket --output-template-file ../global-s3-assets/game-analytics-pipeline.template

echo "------------------------------------------------------------------------------"  
echo "Completed building distribution"
echo "------------------------------------------------------------------------------" 

ls -laR $build_dist_dir
ls -laR $template_dist_dir

