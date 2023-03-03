#!/bin/bash
#
# This script is intended to be run once to setup GCP resources 
# for the PAgCASA-Report-Emailer

usage="$0 <bucket>"

gcs_bucket=${1:?Please provide the GCS bucket: ${usage}}

# Create the GCS bucket if it doesn't exist.
buckets=$(gsutil ls)
mybucket=$gcs_bucket

if [[ "$buckets" == *"gs://$mybucket"* ]]; then
	echo "This GCS bucket already exists: $mybucket"
else
  gsutil mb gs://$mybucket
fi