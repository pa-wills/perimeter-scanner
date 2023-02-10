import boto3
import json
import os

def handler(event, context):
	dynamodb = boto3.resource("dynamodb", region_name = "ap-southeast-2")
	
	inputTableName = os.environ.get("TABLE_TO_SCAN")
#	outputQueueName = os.environ.get("QUEUE_TO_POPULATE")

	# TODO: Scan the derived table.
	inputTable = dynamodb.Table(inputTableName)
	responseScan = inputTable.scan()
	items = responseScan["Items"]
	while 'LastEvaluatedKey' in responseScan:
		responseScan = inputTable.scan(ExclusiveStartKey = responseScan['LastEvaluatedKey'])
		items.extend(responseScan["Items"])

	# TODO: Iterate
		# TODO: For each item, check last scanned date.
		# TODO: If none exists, or if not in last 7 days - enqueue.
		# TODO: Else - continue.
	for item in items:
		print(item)


#  hostsOfInterestTable = dynamodb.Table(hostsOfInterestTableName)
    
  # Step 1: get all the unique host names.
#  responseScan = resultsTable.scan()
#  items = responseScan["Items"]

	# TODO: perhaps also enable to trigger on the worker lambda as well.
