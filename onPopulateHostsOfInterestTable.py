from boto3.dynamodb.conditions import Key

import boto3
import json
import os

def handler(event, context):
  resultsTableName = os.environ.get('TABLE_NAME_RESULTS')
  hostsOfInterestTableName = os.environ.get('TABLE_NAME_HOSTS_OF_INTEREST')

  dynamodb = boto3.resource("dynamodb", region_name = "ap-southeast-2")
  resultsTable = dynamodb.Table(resultsTableName)
  hostsOfInterestTable = dynamodb.Table(hostsOfInterestTableName)
    
  # Step 1: get all the unique host names.
  responseScan = resultsTable.scan()
  items = responseScan["Items"]
  while 'LastEvaluatedKey' in responseScan:
    responseScan = resultsTable.scan(ExclusiveStartKey = responseScan['LastEvaluatedKey'])
    items.extend(responseScan["Items"])
  hosts = []
  for item in items:
    hosts.append(item["host"])
  hosts = list(dict.fromkeys(hosts))
  for host in hosts:
    responseInsert = hostsOfInterestTable.put_item(
      Item = {
        "host" : host
      }
    )
        
    # Step 2: Get the datetime of the first and last values of each host.
    for host in hosts:
      responseQuery = resultsTable.query(
        IndexName = "host-datetime-index",
        KeyConditionExpression = Key("host").eq(str(host))
      )
      responseUpdate = hostsOfInterestTable.update_item(
        Key = {
          "host" : host
        },
        UpdateExpression = "set DatetimeFirst = :r, DatetimeLast = :s",
        ExpressionAttributeValues = {
          ":r": responseQuery["Items"][0]["datetime"],
          ":s": responseQuery["Items"][len(responseQuery["Items"]) - 1]["datetime"]
        }
      )
        
      return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!'),
        'count': len(hosts) #,
      }