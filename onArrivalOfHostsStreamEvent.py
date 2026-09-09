from boto3.dynamodb.conditions import Key

import boto3
import datetime
import os


def handler(event, context):

  hostsOfInterestTableName = os.environ.get("TABLE_NAME_HOSTS_OF_INTEREST")

  dynamodb = boto3.resource("dynamodb")
  hostsOfInterestTable = dynamodb.Table(hostsOfInterestTableName)

  for record in event["Records"]:
    if record["eventName"] != "INSERT":
      continue
    responseQuery = hostsOfInterestTable.query(
      KeyConditionExpression = Key("host").eq(str(record["dynamodb"]["Keys"]["host"]["S"]))
    )
    datetimeString = datetime.datetime.now(datetime.timezone.utc).isoformat()
    if (responseQuery["Items"] == []):
      hostsOfInterestTable.put_item(
        Item = {
          "host": str(record["dynamodb"]["Keys"]["host"]["S"]),
          "DatetimeFirst": datetimeString,
          "DatetimeLast": datetimeString
        }
      )
    else:
      hostsOfInterestTable.update_item(
        Key = {
          "host": str(record["dynamodb"]["Keys"]["host"]["S"])
        },
        UpdateExpression = "set DatetimeLast = :r",
        ExpressionAttributeValues = {
          ":r": datetimeString
        }
      )