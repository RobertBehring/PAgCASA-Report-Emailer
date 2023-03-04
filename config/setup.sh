#!/bin/bash
#
# This script is intended to be run once to setup GCP resources 
# for the PAgCASA-Report-Emailer

usage="$0 <bucket>"
gcs_bucket=${1:?Please provide the GCS bucket: ${usage}}


PROJECT_ID=$(gcloud config get-value project)
PROJECT_NUMBER=YOUR-PROJECT_NUMBER
SERVICE_ACCOUNT="$(gsutil kms serviceaccount -p ${PROJECT_ID})"
REGION=us-west1

# You may need to enable the required IAM permssions and Services by running the following commands
# Enable IAM permissions:
#gcloud iam service-accounts add-iam-policy-binding \
#    ${PROJECT_NUMBER}-compute@developer.gserviceaccount.com \
#    --member MEMBER \
#    --role roles/iam.serviceAccountUser

# gcloud iam service-accounts add-iam-policy-binding \
#    ${PROJECT_NUMBER}-compute@developer.gserviceaccount.com \
#    --member serviceAccount=${PROJECT_NUMBER}-compute@developer.gserviceaccount.com \
#    --role roles/cloudfunctions.admin

#gcloud projects add-iam-policy-binding ${PROJECT_ID} \
#    --member="serviceAccount:${SERVICE_ACCOUNT}" \
#    --role='roles/pubsub.publisher'


# Enable Services
# gcloud services enable run.googleapis.com logging.googleapis.com cloudbuild.googleapis.com storage.googleapis.com pubsub.googleapis.com eventarc.googleapis.com

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
--service-account=${PROJECT_NUMBER}-compute@developer.gserviceaccount.com

# Create Pub/Sub Topic
gcloud pubsub topics create export_to_csv

# Deploy Email CSV Report and Trigger


gcloud functions deploy email-csv \
--gen2 \
--region=$REGION \
--runtime=python310 \
--source=./src/email_csv \
--entry-point send_csv_email \
--trigger-topic=export_to_csv \
--service-account=${PROJECT_NUMBER}-compute@developer.gserviceaccount.com

gcloud scheduler jobs create pubsub export_to_csv \
--schedule="00 7 * * *" \
--location="$REGION" \
--topic export_to_csv \
--message-body="Sent Scheduled Email" 
