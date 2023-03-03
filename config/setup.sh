#!/bin/bash
#
# This script is intended to be run once to setup GCP resources 
# for the PAgCASA-Report-Emailer
# You may need to enable IAM permssions by running the following command

# Enable IAM permissions:
#gcloud iam service-accounts add-iam-policy-binding \
#    PROJECT_NUMBER-compute@developer.gserviceaccount.com \
#    --member MEMBER \
#    --role roles/iam.serviceAccountUser

# gcloud iam service-accounts add-iam-policy-binding \
#    646746772657-compute@developer.gserviceaccount.com \
#    --member serviceAccountyounjada@oregonstate.edu \
#    --role roles/cloudfunctions.admin


usage="$0 <bucket>"
gcs_bucket=${1:?Please provide the GCS bucket: ${usage}}

REGION=us-west1

# Create the GCS bucket if it doesn't exist.
buckets=$(gsutil ls)
mybucket=$gcs_bucket

if [[ "$buckets" == *"gs://$mybucket"* ]]; then
	echo "This GCS bucket already exists: $mybucket"
else
  gsutil mb -l $REGION gs://$mybucket
  echo "Create GCS bucket: $mybucket"
fi

# Make the tables
python3 src/database_BigQuery/DDL.py


# Deploy Export to BQ
echo "Connecting GCS bucket $mybucket to Export to BigQuery Cloud Function"

gcloud functions deploy get-new-upload \
--gen2 \
--region=$REGION \
--runtime=python310 \
--source=./src/export_to_bq \
--entry-point=get_new_data \
--trigger-event-filters="type=google.cloud.storage.object.v1.finalized" \
--trigger-event-filters="bucket=$mybucket" \
--service-account=646746772657-compute@developer.gserviceaccount.com

# Deploy Email CSV Report and Trigger
gcloud functions deploy email-csv \
--gen2 \
--region=$REGION \
--runtime=python310 \
--source=./src/email_csv \
--entry-point send_csv_email \
--trigger-resource export_to_csv \
--trigger-event google.pubsub.topic.publish \
--service-account=646746772657-compute@developer.gserviceaccount.com

gcloud scheduler jobs create pubsub export_to_csv \
--schedule="00 7 * * *" \
--location="$REGION" \
--topic export_to_csv \
--message-body="Sent Scheduled Email" 