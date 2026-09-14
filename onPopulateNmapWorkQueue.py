import boto3
import datetime
import os

thresholdSecs = (3600 * 24 * 7) # I.e. 1 week. TODO: parameterize.


def _asUtc(value):
	# DatetimeLastEnqueued written by older runs is a naive string; treat it as UTC
	# so it can be compared with a timezone-aware "now".
	dt = datetime.datetime.fromisoformat(value)
	if dt.tzinfo is None:
		dt = dt.replace(tzinfo=datetime.timezone.utc)
	return dt


def handler(event, context):
	dynamodb = boto3.resource("dynamodb")
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
	
	
	for item in items:
		# If never enqueued, or not enqueued for thresholdSecs seconds: enqueue.
		now = datetime.datetime.now(datetime.timezone.utc)
		if "DatetimeLastEnqueued" not in item:
			sqsClient.send_message(QueueUrl = outputQueueName, MessageBody = str(item["host"]))
			responseUpdate = inputTable.update_item(
				Key = {
					"host" : str(item["host"])
				},
				UpdateExpression = "set DatetimeLastEnqueued = :r",
				ExpressionAttributeValues = {
					":r": now.isoformat()
				}
			)
			continue

		# If enqueued previously but not yet run to completion: continue.
		# TODO: allow for corner case of first ever run failing. Want retry after thresholdSecs.
		elif "DatetimeLastNmaped" not in item:
			continue
		
		# If not enqueued for > thresholdSecs: enqueue.
		datetimeLastEnqueued = _asUtc(item["DatetimeLastEnqueued"])
		deltaSecsSinceLastEnqueued = int((now - datetimeLastEnqueued).total_seconds())
		if ((deltaSecsSinceLastEnqueued > thresholdSecs)):
			sqsClient.send_message(QueueUrl = outputQueueName, MessageBody = str(item["host"]))
			responseUpdate = inputTable.update_item(
				Key = {
					"host" : str(item["host"])
				},
				UpdateExpression = "set DatetimeLastEnqueued = :r",
				ExpressionAttributeValues = {
					":r": now.isoformat()
				}
			)

	# Enable the nmap triggering rule.
	events = boto3.client("events")
	response = events.enable_rule(Name = workerLambdaRuleName)

	return {
		'statusCode': 200
	}