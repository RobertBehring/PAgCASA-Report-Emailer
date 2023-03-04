import base64
import functions_framework
from google.cloud import bigquery
from google.cloud import storage
import datetime as dt
import io
import csv
import os
import sendgrid
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import *
from google.auth import iam, default
from google.auth.transport import requests
from google.oauth2 import service_account
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

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
    # Get SendGrid API key
    sendgrid_api_key = os.getenv("SENDGRID_API_KEY")

    # Set the project ID where the BigQuery table is stored
    project_id = os.getenv("PROJECT_ID")

    # Set the name of the dataset where the table is stored
    dataset_id = os.getenv("DATASET_ID")

    # Set the name of the table where you want to get the data from
    table_id = os.getenv("TABLE_ID")

    # Set the name of the bucket where you want to store the CSV file
    bucket_name = os.getenv("BUCKET_NAME")

    # Set the name of the bucket where contacts.csv is stored
    contacts_bucket = os.getenv("CONTACTS_BUCKET")

    # Set the name of the .csv file where list of contacts are stored
    contacts_file_name = os.getenv("CONTACTS_FILE_NAME")

    # Set how often (in days) you want the query to run
    query_frequency = os.getenv("QUERY_FREQUENCY")

    # Set the email address you want to send the email from
    sender_email = os.getenv("SENDER_EMAIL")

    # Get the current time
    now = dt.datetime.now()

    # Format the time into a string
    timestamp = now.strftime("%Y-%m-%d %H:%M:%S")
    destination_file_name = timestamp + ".bq_export" + ".csv"

    # Initialize a client for BigQuery
    bigquery_client = bigquery.Client(credentials=credentials())
    
    # Query the data you want to export
    # Below is the query that will export data a a given time interval
    query = "SELECT TestStartTime,ClientIP,ClientLat,ClientLon,DownloadValue,DownloadUnit,UploadValue,UploadUnit,Ping,PingUnit,ServerLatency,ServerLatencyUnit,Isp,IspDownloadAvg,IspUploadAvg FROM `" + dataset_id + "." + table_id + "` WHERE Timestamp > TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL " + str(query_frequency) + " DAY)"
    query_job = bigquery_client.query(query)
    results = query_job.result()

    # Write the results to a CSV file
    csv_file = io.StringIO()
    writer = csv.writer(csv_file)

    # Write header row
    header = [field.name for field in results.schema]
    writer.writerow(header)
    
    # Statistics
    num_records = 0
    downloads = list()
    uploads = list()
    pings = list()

    # Write data rows
    for row in results:
        writer.writerow(list(row.values()))
        num_records += 1
        downloads.append(row["DownloadValue"])
        uploads.append(row["UploadValue"])
        pings.append(row["Ping"])

    # Upload the CSV file with the query to a bucket in GCS
    gcs = storage.Client(credentials=credentials())
    bucket = gcs.bucket(bucket_name)
    blob = bucket.blob(destination_file_name)
    blob.upload_from_string(csv_file.getvalue(), content_type='text/csv')

    # Get the contacts.csv file from the bucket
    bucket = gcs.bucket(contacts_bucket)
    blob = bucket.blob(contacts_file_name)
    csv_data = blob.download_as_string()

    # Parse the CSV data and extract email addresses
    email_list = []
    csv_lines = csv_data.decode().splitlines()
    csv_reader = csv.reader(csv_lines)
    next(csv_reader)
    for row in csv_reader:
        email_list.append(row[0])

    # Create the body of the email
    email_date_now = now.strftime("%A %B %d, %Y")
    email_date_prev = (now - dt.timedelta(days=1)).strftime("%A %B %d, %Y")
    email_body = '<h1><em>Daily Report: </em>Device Broadband Data</h1><br>'\
                f'<strong>{email_date_prev} to {email_date_now}</strong><br>'\
                 '<table cellspacing="2" cellpadding="10" bgcolor="#000000">'\
                    '<tr bgcolor="cccccc">'\
                         '<th valign="center" align="center">Field</th>'\
                         '<th valign="center" align="center">MAX</th>'\
                         '<th valign="center" align="center">MIN</th>'\
                         '<th valign="center" align="center">AVG</th>'\
                    '</tr>'\
                    '<tr bgcolor="ffffff">'\
                         '<td valign="center">Download Value (bps)</td>'\
                        f'<td valign="center" align="center">{"No data" if len(downloads) == 0 else round(max(downloads), 3)}</td>'\
                        f'<td valign="center" align="center">{"No data" if len(downloads) == 0 else round(min(downloads), 3)}</td>'\
                        f'<td valign="center" align="center">{"No data" if len(downloads) == 0 else round(sum(downloads)/len(downloads), 3)}</td>'\
                    '</tr>'\
                    '<tr bgcolor="cccccc">'\
                         '<td valign="center">Upload Value (bps)</td>'\
                        f'<td valign="center" align="center">{"No data" if len(uploads) == 0 else round(max(uploads), 3)}</td>'\
                        f'<td valign="center" align="center">{"No data" if len(uploads) == 0 else round(min(uploads), 3)}</td>'\
                        f'<td valign="center" align="center">{"No data" if len(uploads) == 0 else round(sum(uploads)/len(uploads), 3)}</td>'\
                    '</tr>'\
                    '<tr bgcolor="ffffff">'\
                         '<td valign="center">Ping Time (ms)</td>'\
                        f'<td valign="center" align="center">{"No data" if len(pings) == 0 else round(max(pings), 3)}</td>'\
                        f'<td valign="center" align="center">{"No data" if len(pings) == 0 else round(min(pings), 3)}</td>'\
                        f'<td valign="center" align="center">{"No data" if len(pings) == 0 else round(sum(pings)/len(pings), 3)}</td>'\
                    '</tr>'\
                '</table>'

    # Create the email message
    message = Mail(
        from_email=sender_email,
        to_emails=email_list,
        subject='Daily Report: Device Broadband Data',
        html_content=email_body
    )

    # Encode the contents of the csv file as Base64
    base64_encoded = base64.b64encode(csv_file.getvalue().encode("utf-8")).decode("utf-8")

    # create email attachment and add it to the email message
    attachedFile = Attachment(
        FileContent(base64_encoded),
        FileName(destination_file_name),
        FileType('text/csv'),
        Disposition('attachment')
    )
    message.attachment = attachedFile


    # send email
    sg = SendGridAPIClient(sendgrid_api_key)
    response = sg.send(message)
    print(response.status_code, response.body, response.headers)