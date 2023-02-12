import boto3
import datetime
import json
import nmap
import os

# This is the nmap worker function. It 1. pops a message from the queue it's paired with, 2. attempts to nmap the host referred to within,
# 3. parses the results, 4. Writes the results out to the required tables

def handler(event, context):

    # TODO: establish contexts to the worked queue and output table.
    outputTableName = os.environ.get("RESULTS_TABLE")
    dynamodb = boto3.resource('dynamodb', region_name="ap-southeast-2")
    hostsOfInterestTable = dynamodb.Table(outputTableName)

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
 
    print("nmap - starting")
    nm = nmap.PortScanner()
    nmapResults = nm.scan(message["Body"], '22-443')
    print("nmap - completed")
    print(nmapResults)

    # TODO: Write required results out to the HostPorts table.

    # TODO: Write the current datetime back to the HostsOfInterest table.
    datetimeString = str(datetime.datetime.now().isoformat())
    hostsOfInterestTable.update_item(
        Key = {
          "host": str(message["Body"])
        },
        UpdateExpression = "set DatetimeLastNmaped = :r",
        ExpressionAttributeValues = {
          ":r": datetimeString
        }
      )

    response = sqs.delete_message(QueueUrl = workQueueName, ReceiptHandle = receiptHandle)

    return {
        'statusCode': 200,
        'message': message,
        'nmapOutputs': nmapResults,
        'body': json.dumps('Hello from nmap, mofos!')
    }
