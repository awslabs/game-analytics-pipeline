######################################################################################################################
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
# Permission is hereby granted, free of charge, to any person obtaining a copy of this
# software and associated documentation files (the "Software"), to deal in the Software
# without restriction, including without limitation the rights to use, copy, modify,
# merge, publish, distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so.
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
# INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A
# PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
# HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
######################################################################################################################

import sys
import json
from datetime import datetime
from awsglue.transforms import *
from pyspark.sql.functions import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.dynamicframe import DynamicFrame
from awsglue.job import Job
from pyspark.sql import SparkSession
from pyspark.sql.types import StringType

#sc = SparkContext()
sc = SparkContext.getOrCreate()
sc.setLogLevel("TRACE")
glueContext = GlueContext(sc)
job = Job(glueContext)

args = getResolvedOptions(sys.argv,
    ['JOB_NAME',
    'database_name',
    'raw_events_table_name',
    'analytics_bucket',
    'processed_data_prefix',
    'glue_tmp_prefix'])

job.init(args['JOB_NAME'], args) 

print("Database: {}".format(args['database_name']))
print("Raw Events Table: {}".format(args['raw_events_table_name']))
print("Analytics bucket output path: {}{}".format(args['analytics_bucket'], args['processed_data_prefix']))
print("Glue Temp S3 location: {}{}".format(args['analytics_bucket'], args['glue_tmp_prefix']))

# catalog: database and table names
db_name = args['database_name']
raw_events_table = args['raw_events_table_name']

# Output location
analytics_bucket_output = args['analytics_bucket'] + args['processed_data_prefix']
analytics_bucket_temp_storage = args['analytics_bucket'] + args['glue_tmp_prefix']

# Helper Function replaces the year month day and hour with the one from the timestamp
def applyTransform(rec):
  rec["year"] = datetime.utcfromtimestamp(rec["event"]["event_timestamp"]).year
  rec["month"] = datetime.utcfromtimestamp(rec["event"]["event_timestamp"]).month
  rec["day"] = datetime.utcfromtimestamp(rec["event"]["event_timestamp"]).day
  #rec["hour"] = datetime.utcfromtimestamp(rec["event"]["event_timestamp"]).hour
  return rec

# Create dynamic frame from the source tables 
events = glueContext.create_dynamic_frame.from_catalog(
    database=db_name, 
    table_name=raw_events_table,
    transformation_ctx = "events"
)

# Maps a transformation function over each record to re-build date partitions using the event_timestamp 
# rather than the Firehose ingestion timestamp
#filtered_events_dyf_transformed = Map.apply(frame = filtered_events_dyf, f = applyTransform)

events.printSchema()
record_count = events.count()
print("Record count: {}".format(record_count))

# Avoid errors if Glue Job Bookmark detects no new data to process and records = 0.
if record_count > 0:
    try:
        output = glueContext.write_dynamic_frame.from_options(
            frame = events, 
            connection_type = "s3", 
            connection_options = {
                "path": analytics_bucket_output,
                "partitionKeys": ["application_id", "year", "month", "day"]
            }, 
            format = "glueparquet",
            transformation_ctx = "output"
        )
    except:
        print("There was an error writing out the results to S3")
    else:
        print("Partition saved.")

else:
    print("Glue Job Bookmark detected no new files to process")
    
job.commit()