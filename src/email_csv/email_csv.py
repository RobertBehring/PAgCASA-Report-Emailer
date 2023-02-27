import base64
import functions_framework
from google.cloud import bigquery
from google.cloud import storage
import datetime
from datetime import datetime as dt
import io
import csv
import os
import sendgrid
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import *
from google.auth import iam, default
from google.auth.transport import requests
from google.oauth2 import service_account

# Source: https://cloud.google.com/blog/products/data-analytics/automating-bigquery-exports-to-an-email
def credentials():
    """Gets credentials to authenticate Google APIs.
 
    Args:
        None
        
    Returns:
        Credentials to authenticate the API.
    """
    # Get Application Default Credentials if running in Cloud Functions
    if os.getenv("IS_LOCAL") is None:
        credentials, project = default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
    # To use this file locally set IS_LOCAL=1 and populate env var GOOGLE_APPLICATION_CREDENTIALS 
    # with path to service account json key file
    else:
        credentials = service_account.Credentials.from_service_account_file(
            os.getenv("GOOGLE_APPLICATION_CREDENTIALS"), scopes=["https://www.googleapis.com/auth/cloud-platform"],
        )
    return credentials

# Triggered from a message on a Cloud Pub/Sub topic.
@functions_framework.cloud_event
def send_csv_email(cloud_event):
    # Set your project and dataset
    project_id = "cs467-capstone-dummy-data"
    dataset_id = "DeviceBroadbandData"
    table_id = "Multistream"
    bucket_name = "bquery_csv_export"
    # Get the current time
    now = dt.now()

    # Format the time into a string
    timestamp = now.strftime("%Y-%m-%d %H:%M:%S")
    destination_file_name = timestamp + ".bq_export" + ".csv"

    # Initialize a client for BigQuery
    bigquery_client = bigquery.Client(credentials=credentials())
    
    # Query the data you want to export
    # Commented out below is the query that will export all data
    # query = "SELECT * FROM `" + dataset_id + "." + table_id + "`"
    # Commneted out below is the query that will export data from the last 7 days
    query = "SELECT Timestamp,TestStartTime,ClientIP,ClientLat,ClientLon,DownloadValue,DownloadUnit,UploadValue,UploadUnit,Ping,PingUnit,ServerLatency,ServerLatencyUnit,Isp,IspDownloadAvg,IspUploadAvg FROM `" + dataset_id + "." + table_id + "` WHERE Timestamp > TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)"
    query_job = bigquery_client.query(query)
    results = query_job.result()

    # Write the results to a CSV file
    csv_file = io.StringIO()
    writer = csv.writer(csv_file)

    # Write header row
    header = [field.name for field in results.schema]
    writer.writerow(header)

    # Write data rows
    for row in results:
        writer.writerow(list(row.values()))

    # Upload the CSV file to a bucket in GCS
    gcs = storage.Client(credentials=credentials())
    bucket = gcs.bucket(bucket_name)
    blob = bucket.blob(destination_file_name)
    blob.upload_from_string(csv_file.getvalue(), content_type='text/csv')


    # print("Exported data to: " + "gs://" + bucket_name + "/" + destination_file_name)
    
    # List of recipients for the email
    recipients = ['recipient1@mail.com', 'recipient2@mail.com', 'recipient3@mail.com']

    # Create the email message
    message = Mail(
        from_email='from_address@mail.com',
        to_emails= recipients,
        subject='BigQuery Export',
        html_content='<strong>This is a test email with a CSV BigQuery Export</strong>'
    )

    # Encode the contents of the csv file as Base64
    base64_encoded = base64.b64encode(csv_file.getvalue().encode("utf-8")).decode("utf-8")

    # create attachment
    attachedFile = Attachment(
        FileContent(base64_encoded),
        FileName(destination_file_name),
        FileType('text/csv'),
        Disposition('attachment')
    )
    message.attachment = attachedFile


    # send email
    sg = SendGridAPIClient('SENDGRID_API_KEY')
    response = sg.send(message)
    print(response.status_code, response.body, response.headers)