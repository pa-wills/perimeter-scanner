from boto3.dynamodb.conditions import Key

import boto3
import datetime
import json
import os


def handler(event, context):

  hostPortsOfInterestTableName = os.environ.get("TABLE_NAME_HOSTPORTS_OF_INTEREST")

  dynamodb = boto3.resource("dynamodb", region_name = "ap-southeast-2")
  hostPortsOfInterestTable = dynamodb.Table(hostPortsOfInterestTableName)

  for record in event["Records"]:
    if record["eventName"] != "INSERT": 
      continue
    responseQuery = hostPortsOfInterestTable.query(
      KeyConditionExpression = Key("composite_HostIpUdpTcp").eq(str(record["dynamodb"]["Keys"]["composite_HostIpUdpTcp"]["S"]))
    )
    datetimeString = str(datetime.datetime.now().isoformat())
    if (responseQuery["Items"] == []):
      hostPortsOfInterestTable.put_item(
        Item = {
          "composite_HostIpUdpTcp": str(record["dynamodb"]["Keys"]["composite_HostIpUdpTcp"]["S"]),
          "DatetimeFirst": datetimeString,
          "DatetimeLast": datetimeString
        }
      )
    else:
      hostPortsOfInterestTable.update_item(
        Key = {
          "composite_HostIpUdpTcp": str(record["dynamodb"]["Keys"]["composite_HostIpUdpTcp"]["S"])
        },
        UpdateExpression = "set DatetimeLast = :r",
        ExpressionAttributeValues = {
          ":r": datetimeString
        }
      )