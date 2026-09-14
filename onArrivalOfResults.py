import boto3
import csv
import datetime
import io
import os

# Fields recon-ng's reporting/csv module emits, in order (HEADERS True).
COLUMNS = ["host", "ip_address", "region", "country", "latitude", "longitude", "notes", "module"]


def handler(event, context):

  tableName = str(os.environ.get('TABLE_NAME'))
  now = datetime.datetime.now(datetime.timezone.utc)
  ttl = int(now.timestamp()) + int(os.environ.get('DYNAMODB_TTL_OFFSET'))  # I.e. Now + offset.
  datetimeString = now.isoformat()

  s3 = boto3.resource("s3")
  s3Client = boto3.client("s3")
  dynamodb = boto3.resource("dynamodb")
  table = dynamodb.Table(tableName)

  bucketName = str(event["Records"][0]["s3"]["bucket"]["name"])
  objectKey = str(event["Records"][0]["s3"]["object"]["key"])
  print("Bucket Name: " + bucketName)
  print("Object Key: " + objectKey)

  rawCsvData = s3Client.get_object(Bucket=bucketName, Key=objectKey)["Body"].read().decode("utf-8")

  for tokens in csv.reader(io.StringIO(rawCsvData)):
    if not tokens or tokens[0] == "host":  # skip blanks and the header row
      continue
    if len(tokens) < len(COLUMNS):
      print("skipping short row: " + repr(tokens))
      continue
    print(tokens)
    item = {name: tokens[i] for i, name in enumerate(COLUMNS)}
    item["datetime"] = datetimeString
    item["ttl"] = ttl
    table.put_item(Item=item)

  s3.Object(bucketName, objectKey).delete()
