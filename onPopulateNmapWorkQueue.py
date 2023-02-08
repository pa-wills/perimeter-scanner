import boto3
import json
import os

def handler(event, context):

	# TODO: Scan the derived table.
	# TODO: Iterate
		# TODO: For each item, check last scanned date.
		# TODO: If none exists, or if not in last 7 days - enqueue.
		# TODO: Else - continue.
	# TODO: perhaps also enable to trigger on the worker lambda as well.
