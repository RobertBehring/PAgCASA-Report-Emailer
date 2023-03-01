# -- PAgCASA DeviceBroadbandData_DDL.sql
# -- Author(s): Robert Behring, Jada Young, Eric Riemer
# -- Date: 02/01/2023
# -- Note: Tables are created using BigQuery dialect and Python's BigQuery
# --        API. 
# -- CITATION: Code to create all BigQuery Tables adapted from below citation
# --    Title: Create and use tables
# --    Author: Google Cloud Guides
# --    URL: https://cloud.google.com/bigquery/docs/tables
# --    Last updated: 2023-01-31 UTC
import os
from google.cloud import bigquery
from dotenv import load_dotenv

load_dotenv()

dataset = os.getenv("DATASET_NAME")
ndt7_table_name = os.getenv("NDT7_TABLE_NAME")
multistream_table_name = os.getenv("MULTISTREAM_TABLE_NAME")

client = bigquery.Client()
# -- #####################################################
# -- TABLE PARAMETERS
# -- #####################################################
project_dataset = client.project + '.' + dataset
# -- -----------------------------------------------------
# -- Table NDT-7
# -- -----------------------------------------------------
ndt7_table_id = project_dataset + '.' + ndt7_table_name

ndt7_schema = [
    bigquery.SchemaField("MinRTTUnit", "STRING", mode="NULLABLE"),
    bigquery.SchemaField("MinRTTValue", "FLOAT", mode="NULLABLE"),
    bigquery.SchemaField("DownloadRetransValue", "INTEGER", mode="NULLABLE"),
    bigquery.SchemaField("UploadError", "STRING", mode="NULLABLE"),
    bigquery.SchemaField("UploadValue", "FLOAT", mode="NULLABLE"),
    bigquery.SchemaField("DownloadRetransUnit", "STRING", mode="NULLABLE"),
    bigquery.SchemaField("DownloadUnit", "STRING", mode="NULLABLE"),
    bigquery.SchemaField("ClientIP", "STRING", mode="NULLABLE"),
    bigquery.SchemaField("UploadUnit", "STRING", mode="NULLABLE"),
    bigquery.SchemaField("DownloadError", "STRING", mode="NULLABLE"),
    bigquery.SchemaField("DownloadValue", "FLOAT", mode="NULLABLE"),
    bigquery.SchemaField("TestEndTime", "DATETIME", mode="NULLABLE"),
    bigquery.SchemaField("ServerName", "STRING", mode="NULLABLE"),
    bigquery.SchemaField("MurakamiLocation", "STRING", mode="NULLABLE"),
    bigquery.SchemaField("ServerIP", "STRING", mode="NULLABLE"),
    bigquery.SchemaField("MurakamiDeviceID", "STRING", mode="NULLABLE"),
    bigquery.SchemaField("DownloadUUID", "STRING", mode="NULLABLE"),
    bigquery.SchemaField("MurakamiNetworkType", "STRING", mode="NULLABLE"),
    bigquery.SchemaField("TestName", "STRING", mode="NULLABLE"),
    bigquery.SchemaField("MurakamiConnectionType", "STRING", mode="NULLABLE"),
    bigquery.SchemaField("TestStartTime", "DATETIME", mode="NULLABLE")
]

# -- -----------------------------------------------------
# -- Table Multistream
# -- -----------------------------------------------------
multistream_table_id = project_dataset + '.' + multistream_table_name

multistream_schema = [
    bigquery.SchemaField("Country", "STRING", mode="NULLABLE"),
    bigquery.SchemaField("LoggedIn", "INTEGER", mode="NULLABLE"),
    bigquery.SchemaField("IspUploadAvg", "INTEGER", mode="NULLABLE"),
    bigquery.SchemaField("IspDownloadAvg", "INTEGER", mode="NULLABLE"),
    bigquery.SchemaField("IspRating", "FLOAT", mode="NULLABLE"),
    bigquery.SchemaField("ClientLat", "FLOAT", mode="NULLABLE"),
    bigquery.SchemaField("ServerLatencyUnit", "STRING", mode="NULLABLE"),
    bigquery.SchemaField("ServerLatency", "FLOAT", mode="NULLABLE"),
    bigquery.SchemaField("ServerDistance", "FLOAT", mode="NULLABLE"),
    bigquery.SchemaField("ServerID", "INTEGER", mode="NULLABLE"),
    bigquery.SchemaField("ServerSponsor", "STRING", mode="NULLABLE"),
    bigquery.SchemaField("ServerCountryCode", "STRING", mode="NULLABLE"),
    bigquery.SchemaField("MurakamiLocation", "STRING", mode="NULLABLE"),
    bigquery.SchemaField("BytesReceived", "INTEGER", mode="NULLABLE"),
    bigquery.SchemaField("TimeStamp", "TIMESTAMP", mode="NULLABLE"),
    bigquery.SchemaField("Share", "STRING", mode="NULLABLE"),
    bigquery.SchemaField("MurakamiDeviceID", "STRING", mode="NULLABLE"),
    bigquery.SchemaField("BytesSent", "INTEGER", mode="NULLABLE"),
    bigquery.SchemaField("Isp", "STRING", mode="NULLABLE"),
    bigquery.SchemaField("PingUnit", "STRING", mode="NULLABLE"),
    bigquery.SchemaField("ServerHost", "STRING", mode="NULLABLE"),
    bigquery.SchemaField("ServerCountry", "STRING", mode="NULLABLE"),
    bigquery.SchemaField("ServerLat", "FLOAT", mode="NULLABLE"),
    bigquery.SchemaField("ClientLon", "FLOAT", mode="NULLABLE"),
    bigquery.SchemaField("ClientIP", "STRING", mode="NULLABLE"),
    bigquery.SchemaField("ServerName", "STRING", mode="NULLABLE"),
    bigquery.SchemaField("Ping", "FLOAT", mode="NULLABLE"),
    bigquery.SchemaField("UploadValue", "FLOAT", mode="NULLABLE"),
    bigquery.SchemaField("Rating", "INTEGER", mode="NULLABLE"),
    bigquery.SchemaField("TestEndTime", "DATETIME", mode="NULLABLE"),
    bigquery.SchemaField("UploadUnit", "STRING", mode="NULLABLE"),
    bigquery.SchemaField("MurakamiConnectionType", "STRING", mode="NULLABLE"),
    bigquery.SchemaField("DownloadValue", "FLOAT", mode="NULLABLE"),
    bigquery.SchemaField("MurakamiNetworkType", "STRING", mode="NULLABLE"),
    bigquery.SchemaField("ServerLon", "FLOAT", mode="NULLABLE"),
    bigquery.SchemaField("ServerURL", "STRING", mode="NULLABLE"),
    bigquery.SchemaField("TestName", "STRING", mode="NULLABLE"),
    bigquery.SchemaField("TestStartTime", "DATETIME", mode="NULLABLE"),
    bigquery.SchemaField("DownloadUnit", "STRING", mode="NULLABLE")
]


if __name__ == '__main__':
    client.delete_dataset(
        project_dataset, delete_contents=True, not_found_ok=True)
    print("Deleted dataset '{}'.".format(project_dataset))

    dataset = bigquery.Dataset(project_dataset)
    dataset.location = "us-west1"
    dataset = client.create_dataset(dataset, timeout=30)
    print("Created dataset {}.{}".format(client.project, dataset.dataset_id))


    multistream_table = bigquery.Table(multistream_table_id, schema=multistream_schema)
    multistream_table = client.create_table(multistream_table)
    print(
        "Created table {}.{}.{}".format(multistream_table.project, multistream_table.dataset_id, multistream_table.table_id)
    )

    ndt7_table = bigquery.Table(ndt7_table_id, schema=ndt7_schema)
    ndt7_table = client.create_table(ndt7_table)
    print(
        "Created table {}.{}.{}".format(ndt7_table.project, ndt7_table.dataset_id, ndt7_table.table_id)
    )