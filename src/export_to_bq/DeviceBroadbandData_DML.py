from google.cloud import bigquery

client = bigquery.Client()
# Project
project_id = "cs467-capstone-dummy-data"
# Dataset (Database)
dataset_id = "DeviceBroadbandData"
# Tables
    # NDT-7
ndt7_table_id = '.'.join([project_id, dataset_id, "NDT-7"])
ndt7_table_query_id = '`' + ndt7_table_id + '`'
ndt7_table = client.get_table(ndt7_table_id)
    # Multistream Table
multistream_table_id = '.'.join([project_id, dataset_id, "Multistream"])
multistream_table_query_id = '`' + multistream_table_id + '`'
multistream_table = client.get_table(multistream_table_id)

"""#### General Table Functions ###############################################"""
def display_table_info(table: bigquery.Table) -> None:
    """
    display_table_info() prints the table information of the BigQuery table 
    provided. 
    
    table: bigquery.Table class
    return: None
    """
    table_info = table.project + table.dataset_id + table.table_id
    table_schema = table.schema
    table_description = table.description
    table_rows = table.num_rows
    print("-----------------------------------------------------------")
    print("Got table {}\n".format(table_info))
    for schema in table_schema:
        print(schema)
    print()
    print("Table description: {}".format(table_description))
    print("Table has {} rows\n".format(table_rows))
    print("-----------------------------------------------------------")

def send_query(query: str) -> bigquery.QueryJob.result:
    """
    send_query() takes a given query string and creates a QueryJob class based
    on the given BigQuery query. The function then executes the query job and
    returns the iterator of the QueryJob class upon completion of the query job
    
    query: BigQuery query string
    return: QueryJob.result() iterator
    """
    query_job = client.query(query)
    return query_job.result()

"""#### CREATE ################################################################"""
def insert_json_uri(table: bigquery.Table, table_id: str, bucket_uri: str) -> None:
    """
    insert_json_uri() takes as parameters table, table_id, and bucket uri and
    inserts the data from the GCS bucket uri into the given BigQuery table.

    table: destination BigQuery table
    table_id: destination BigQuery table identification
    bucket_uri: URI of the GCS bucket from which to obtain data
    return: None
    """
    job_config = bigquery.LoadJobConfig(
        schema=table.schema,
        source_format=bigquery.SourceFormat.NEWLINE_DELIMITED_JSON,
    )
    
    load_job = client.load_table_from_uri(
        bucket_uri,
        table_id,
        location="us-west1",   # Must match the destination dataset location
        job_config=job_config,
    )   # Make an API request.

    try:
        load_job.result()  # Waits for the job to complete.
    except:
        print("ERROR:")
        for error in load_job.errors:
            for reason in error.keys():
                print(reason + ": " + error[reason])
            print('\n')
        return

    destination_table = client.get_table(table_id)
    print("Loaded {} rows.".format(destination_table.num_rows))

"""#### READ ##################################################################"""
# Query Statements
multistream_queries = {
    "selectAll": """SELECT * FROM {}\n""".format(multistream_table_query_id),
    "selectDown/Upload": """SELECT TestName, ClientIP, TestStartTime, TestEndTime, DownloadValue, DownloadUnit, UploadValue, UploadUnit FROM {}\n""".format(multistream_table_query_id),
    "requested": """SELECT
                        Timestamp,
                        TestStartTime,
                        ClientIP,
                        ClientLat,
                        ClientLon,
                        DownloadValue,
                        DownloadUnit,
                        UploadValue,
                        UploadUnit,
                        Ping,
                        PingUnit,
                        ServerLatency,
                        ServerLatencyUnit,
                        Isp,
                        IspDownloadAvg,
                        IspUploadAvg
                    FROM
                        `cs467-capstone-dummy-data.DeviceBroadbandData.Multistream`
                    WHERE
                        Timestamp > TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 15 DAY) AND Timestamp <= CURRENT_TIMESTAMP()
                    ORDER BY
                        Timestamp"""
}
"""Time Selection"""
times = {
    "daily": """WHERE TestStartTime > TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 DAY)\n""",
    "weekly": """WHERE TestStartTime > TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)\n""",
    "monthly": """WHERE TestStartTime > TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 31 DAY)\n""",
    "yearly": """WHERE TestStartTime > TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 365 DAY)\n"""
}

"""#### Testing Functions #####################################################"""
def test_queries(query_dict: dict) -> None:
    """
    test_queries() runs through all of the queries in a given query dictionary
    and prints the results to STDOUT.

    query_dict: dictionary of query statements to test
    return: None
    """
    limiter = "LIMIT 1"
    for query in query_dict.keys():
        print("Running Query: {}".format(query))
        for row in send_query(query_dict[query]+limiter):
            print(row)
        print("-----------------------------------------------------------")


if __name__ == '__main__':
    isTesting = False

    display_table_info(multistream_table)
    display_table_info(ndt7_table)

    """
      -------------------------------------------------------------------------
    EXAMPLE: How to insert bucket uri (in JSON format) into table
        The below 2 lines of code demonstrate how to insert data from GCS
        buckets (via a GCS bucket URI i.e. gs://bucket_name/bucket_id). 
            1. Determine the uri(s) that you wish to transfer
            2. Determine the table where you are going to send the data
                a. Table data variables passed into insert_json_uri() can be 
                   found at the top of this program
            3. Run the insert_json_uri() function. Take care to include the
               following input:
                a. table: the table where the data is being sent
                    i. data format MUST match schema of table, otherwise 
                       an error message will prompt
                b. table_id: the table identification string.
                    i. 'project_id.dataset_id.table_name'
                c. bucket_uri: the URI location of the GCS bucket
                    i. 'gs://bucket_name/bucket_id'
        Upon completion you will either receive a number of rows in the table
        as a sign of completion. OR you will receive an error message, the 
        error message is in a dictionary format. The error message is parsed
        by the insert_bucket_uri function and printed to STDOUT.
    """
    # bucket_uri = "gs://pagcasa-dummy-data/200-ooklaRandomizedData.JSON"
    # insert_json_uri(multistream_table, multistream_table_id, bucket_uri)

    # -------------------------------------------------------------------------
    if isTesting:
        test_queries(multistream_queries)  # run all read queries for test purposes
