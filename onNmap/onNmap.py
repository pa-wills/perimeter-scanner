import boto3
import json
import nmap
import os

def handler(event, context):

    # TODO: establish contexts to the worked queue and output table.
    outputTableName = os.environ.get("RESULTS_TABLE")
    dynamodb = boto3.resource('dynamodb', region_name="ap-southeast-2")
    table = dynamodb.Table(outputTableName)
    workQueueName = os.environ.get("WORK_QUEUE")
    sqs = boto3.client('sqs')

    # If queue depth == 0, continue.
    if (sqs.get_queue_attributes(
        QueueUrl = workQueueName,
        AttributeNames = ["ApproximateNumberOfMessages"])["Attributes"]["ApproximateNumberOfMessages"] == "0"
    ):
        # TODO: Maybe it should also disable the trigger for this function.
        return {
            'statusCode': 200,
            'body': json.dumps('Work queue was zero-depth. Exiting')
        }

    # TODO: Pop from queue, obtain hostname.
    response = sqs.receive_message(QueueUrl = workQueueName, MaxNumberOfMessages = 1)
    message = response['Messages'][0]
    receiptHandle = message['ReceiptHandle']
 
    nm = nmap.PortScanner()
    nmapResults = nm.scan(message["Body"], '22-443')

    # TODO: Write required messages to table.

    # TODO: Delete message from queue.
    response = sqs.delete_message(QueueUrl = workQueueName, ReceiptHandle = receiptHandle)

    return {
        'statusCode': 200,
        'message': message,
        'nmapOutputs': nmapResults,
        'body': json.dumps('Hello from nmap, mofos!')
    }
