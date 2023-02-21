import boto3
import csv
import datetime
import json
import os

def handler(event, context):

  tableName = str(os.environ.get('TABLE_NAME'))
  ttl = int(datetime.datetime.now().timestamp()) + int(os.environ.get('DYNAMODB_TTL_OFFSET')) # I.e. Now + offset.

  s3 = boto3.resource("s3")
  s3Client = boto3.client("s3")
  
  dynamodb = boto3.resource('dynamodb', region_name="ap-southeast-2")
  table = dynamodb.Table(tableName)

  datetimeString = str(datetime.datetime.now().isoformat())
  bucketName = str(event["Records"][0]["s3"]["bucket"]["name"])
  objectKey = str(event["Records"][0]["s3"]["object"]["key"])

  response = s3Client.get_object(Bucket = bucketName, Key = objectKey)
  rawCsvData = str(response["Body"].read())

  print("Bucket Name: " + bucketName)
  print("Object Key: " + objectKey)

  strippedCsvData = rawCsvData.strip("b\'").strip("\'")
  lines = strippedCsvData.split("\\r\\n")
  for line in lines:

    # Tokenize data ready for ingestion.
    line = line.replace("\"", "")
    if (line == ""): continue
    tokens = line.split(",")
    if (tokens[0] == "host"): continue
    print(tokens)
    
    # Ingest
    response = table.put_item(
      Item = {
        'datetime': datetimeString,
        'host': tokens[0],
        'ip_address': tokens[1],
        'region': tokens[2],
        'country': tokens[3],
        'latitude': tokens[4],
        'longitude': tokens[5],
        'notes': tokens[6],
        'module': tokens[7],
        'ttl': ttl
      }
    )
    s3.Object(bucketName, objectKey).delete()