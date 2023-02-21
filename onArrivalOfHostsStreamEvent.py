from boto3.dynamodb.conditions import Key

import boto3
import datetime
import json
import os


def handler(event, context):

  hostsOfInterestTableName = os.environ.get("TABLE_NAME_HOSTS_OF_INTEREST")

  dynamodb = boto3.resource("dynamodb", region_name = "ap-southeast-2")
  hostsOfInterestTable = dynamodb.Table(hostsOfInterestTableName)

  for record in event["Records"]:
    if record["eventName"] != "INSERT": 
      continue
    responseQuery = hostsOfInterestTable.query(
      KeyConditionExpression = Key("host").eq(str(record["dynamodb"]["Keys"]["host"]["S"]))
    )
    datetimeString = str(datetime.datetime.now().isoformat())
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