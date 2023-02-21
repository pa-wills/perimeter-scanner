import boto3
import datetime
import json
import os

thresholdSecs = (3600 * 24 * 7) # I.e. 1 week

def handler(event, context):
	dynamodb = boto3.resource("dynamodb", region_name = "ap-southeast-2")
	sqsClient = boto3.client("sqs")
	
	inputTableName = os.environ.get("TABLE_TO_SCAN")
	outputQueueName = os.environ.get("QUEUE_TO_POPULATE")
	workerLambdaRuleName = os.environ.get("RULE_TRIGGER_WORKER_LAMBDA")

	# Scan the derived table.
	inputTable = dynamodb.Table(inputTableName)
	responseScan = inputTable.scan()
	items = responseScan["Items"]
	while 'LastEvaluatedKey' in responseScan:
		responseScan = inputTable.scan(ExclusiveStartKey = responseScan['LastEvaluatedKey'])
		items.extend(responseScan["Items"])
	
	# Iterate. If never nmaped, or not for thresholdSecs seconds: enqueue.
	for item in items:
		if "DatetimeLastNmaped" not in item:
			sqsClient.send_message(QueueUrl = outputQueueName, MessageBody = str(item["host"]))
			continue
		
		now = datetime.datetime.now()
		datetimeLastNmaped = datetime.datetime.fromisoformat(item["DatetimeLastNmaped"])
		deltaSecs = int((now - datetimeLastNmaped).total_seconds())
		if (deltaSecs > thresholdSecs):
			sqsClient.send_message(QueueUrl = outputQueueName, MessageBody = str(item["host"]))

	# TODO: Implement enablement of the nmap triggering rule.
	events = boto3.client("events")
	response = events.enable_rule(Name = workerLambdaRuleName)

	return {
		'statusCode': 200
	}