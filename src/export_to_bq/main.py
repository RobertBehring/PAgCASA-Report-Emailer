import functions_framework
import json
from google.cloud import storage
from google.cloud import bigquery
import DeviceBroadbandData_DML as DML
import time, random

def get_file_data(bucket, name):
   # Connect to the storage bucket and retrieve the file data
   storage_client = storage.Client()
   gcs_bucket = storage_client.bucket(bucket)
   blob = gcs_bucket.blob(name)

   # Retrieve the contents of the file
   file_content = blob.download_as_string().decode("utf-8")

   # Parse the contents of the file as a JSON object
   json_content = json.loads(file_content)

   print(json_content)
   return blob.self_link()

# Triggered by a change in a storage bucket
@functions_framework.cloud_event
def get_new_data(cloud_event):
   data = cloud_event.data

   event_id = cloud_event["id"]
   event_type = cloud_event["type"]

   bucket = data["bucket"]
   name = data["name"]
   timeCreated = data["timeCreated"]

   print(f"Bucket: {bucket}")
   print(f"File: {name}")
   
   uri = f"gs://{bucket}/{name}"
   print(uri)

   while True:
      # Try to insert the data
      try:
         if "multi-stream" in name:
            DML.insert_json_uri(DML.multistream_table, DML.multistream_table_id, uri)
         
         elif "ndt7" in name:
            DML.insert_json_uri(DML.ndt7_table, DML.ndt7_table_id, uri)
         break
      except:
         # Sleep for a while then try again
         time.sleep(random.randint(1, 10))
