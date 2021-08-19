#!/bin/bash
#
# This assumes all of the OS-level configuration has been completed and git repo has already been cloned
#
# This script should be run from the repo's deployment directory
# cd deployment
# ./run-unit-tests.sh
#

# Get reference for all important folders
template_dir="$PWD"
source_dir="$template_dir/../source"

echo "------------------------------------------------------------------------------"
echo "[Init] Clean old dist and node_modules folders"
echo "------------------------------------------------------------------------------"
echo "find $source_dir/services -iname "node_modules" -type d -exec rm -r "{}" \; 2> /dev/null"
find $source_dir/services -iname "node_modules" -type d -exec rm -r "{}" \; 2> /dev/null
echo "find $source_dir/services -iname "dist" -type d -exec rm -r "{}" \; 2> /dev/null"
find $source_dir/services -iname "dist" -type d -exec rm -r "{}" \; 2> /dev/null
echo "find ../ -type f -name 'package-lock.json' -delete"
find $source_dir/services -type f -name 'package-lock.json' -delete
echo "find $source_dir/resources -iname "node_modules" -type d -exec rm -r "{}" \; 2> /dev/null"
find $source_dir/resources -iname "node_modules" -type d -exec rm -r "{}" \; 2> /dev/null
echo "find $source_dir/resources -iname "dist" -type d -exec rm -r "{}" \; 2> /dev/null"
find $source_dir/resources -iname "dist" -type d -exec rm -r "{}" \; 2> /dev/null
echo "find ../ -type f -name 'package-lock.json' -delete"
find $source_dir/resources -type f -name 'package-lock.json' -delete
echo "find $source_dir/simulator -iname "node_modules" -type d -exec rm -r "{}" \; 2> /dev/null"
find $source_dir/simulator -iname "node_modules" -type d -exec rm -r "{}" \; 2> /dev/null
echo "find $source_dir/simulator -iname "dist" -type d -exec rm -r "{}" \; 2> /dev/null"
find $source_dir/simulator -iname "dist" -type d -exec rm -r "{}" \; 2> /dev/null
echo "find ../ -type f -name 'package-lock.json' -delete"
find $source_dir/simulator -type f -name 'package-lock.json' -delete

echo "------------------------------------------------------------------------------"
echo "[Test] Services - Analytics Processing Function"
echo "------------------------------------------------------------------------------"
cd $source_dir/services/analytics-processing
npm install
npm test
echo "------------------------------------------------------------------------------"
echo "[Test] Services - Admin API Function"
echo "------------------------------------------------------------------------------"
cd $source_dir/services/api/admin
npm install
npm test
echo "------------------------------------------------------------------------------"
echo "[Test] Services - Lambda Authorizer Function"
echo "------------------------------------------------------------------------------"
cd $source_dir/services/lambda-authorizer
npm install
npm test
echo "------------------------------------------------------------------------------"
echo "[Test] Services - Glue Partition Creator Function"
echo "------------------------------------------------------------------------------"
cd $source_dir/services/data-lake/glue-partition-creator
npm install
npm test
echo "------------------------------------------------------------------------------"
echo "[Test] Services - Events Processing Function"
echo "------------------------------------------------------------------------------"
cd $source_dir/services/events-processing
npm install
npm test
