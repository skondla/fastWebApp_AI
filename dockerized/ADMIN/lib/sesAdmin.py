#!/usr/bin/env python3
#Author: skondla@me.com
#Purpose: Simple Email Service Administration
import os
import boto3
from botocore.exceptions import ClientError
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from boto.beanstalk import response
import json


def sesClient():
	ses = boto3.client('ses')
	return ses

def sendEmail(subject,content):
	# def sendEmail(subject,message):
	client = sesClient()
	#toAddr = emailList('email.to')
	toAddr = open(os.environ['SES_DIR']+'/recipients.list', 'r')
	toAddr = ' '.join(map(str, toAddr))
	# toAddr = emailList('/home/admin/jobs/ses/recipients.list')
	# toAddr = open('/home/admin/jobs/ses/recipients.list', 'r')
	#ccAddr = emailList('email.cc')
	ccAddr = open(os.environ['SES_DIR']+'/cc.list', 'r')
	ccAddr = ' '.join(map(str, ccAddr))
	#bccAddr = emailList('email.bcc')
	bccAddr = open(os.environ['SES_DIR']+'/bcc.list', 'r')
	bccAddr = ' '.join(map(str, bccAddr))
	response = client.send_email(
		Destination={
			'BccAddresses':
				#bccAddr,
				bccAddr.split(','),
			'CcAddresses':
				#ccAddr,
				ccAddr.split(','),
			'ToAddresses':
				toAddr.split(',')
				#toAddr,
		},
		Message={
			'Body': {
				'Text': {
					'Charset': 'UTF-8',
					'Data': '%s' % content,
				},
			},
			'Subject': {
				'Charset': 'UTF-8',
				'Data': '%s' % subject,
			},
		},
		Source='skondla@me.com',
		#SourceArn='arn:aws:ses:us-east-1:1234567890:identity/skondla@me.com',
	)
	return response


# print(response)

def emailList(fileName):
	""" Pass email distribution file name(s)"""
	with open(fileName) as f:
		emailAddr = [line.rstrip() for line in f]
	# print('EMAILS: ', json.dumps(emailAddr))
	return emailAddr

def sendEmailAttach(fileName, content):
	client = sesClient()
	toAddr = emailList(os.environ['SES_DIR']+'/email.to')
	# toAddr = emailList('/home/admin/jobs/ses/recipients.list')
	# toAddr = open('/home/admin/jobs/ses/recipients.list', 'r')
	ccAddr = emailList(os.environ['SES_DIR']+'/email.cc')
	bccAddr = emailList(os.environ['SES_DIR']+'/email.bcc')
	message = MIMEMultipart()
	message['Subject'] = content[0]
	message['From'] = 'skondla@me.com'
	message['To'] = ', '.join(toAddr)
	# message body
	part = MIMEText(content[1], 'html')
	message.attach(part)
	# attachment
	if fileName:  # if bytestring available
		part = MIMEApplication(open(fileName, 'rb').read())
		part.add_header('Content-Disposition', 'attachment', filename=fileName)
		message.attach(part)

		response = client.send_raw_email(
			Destination={
				'BccAddresses':
					bccAddr,
				'CcAddresses':
					ccAddr,
				'ToAddresses':
					toAddr,
			},
			RawMessage={
				'Data': message.as_string()
			}
			# Source='skondla@me.com',
			# SourceArn='arn:aws:ses:us-east-1:1234567890:identity/skondla@me.com',
		)

	else:  # if file provided
		part = MIMEApplication(str.encode('attachment_string'))

	return response

def sendRawEmail(fileName,subject,content):
	toAddr = open(os.environ['SES_DIR']+'/recipients.list', 'r')
	toAddr = ' '.join(map(str, toAddr))
	#print('toAddr: ', toAddr)
	print('content: ', content)
	# Replace sender@example.com with your "From" address.
	# This address must be verified with Amazon SES.
	SENDER = "skondla@me.com"
	#SENDER = "skondla@me.com"
	# Replace recipient@example.com with a "To" address. If your account
	# is still in the sandbox, this address must be verified.
	RECIPIENT = toAddr
	# CONFIGURATION_SET = "ConfigSet"
	# If necessary, replace us-west-2 with the AWS Region you're using for Amazon SES.
	AWS_REGION = os.environ['AWS_REGION']
	# The subject line for the email.
	SUBJECT = subject
	#SUBJECT = content[0]
	# The full path to the file that will be attached to the email.
	ATTACHMENT = "" + fileName + ""
	# ATTACHMENT = "/Users/skondla/OneDrive/Programming/aws/ses/assets_diff_locations.xlsx"
	# The email body for recipients with non-HTML email clients.
	BODY_TEXT = content
	# The HTML body of the email.
	BODY_HTML = """\
    <html>
    <head></head>
    <body>
    <h1>Hello!</h1>
    <p>{content}</p>
    </body>
    </html>
    """.format(content=content)
	# The character encoding for the email.
	CHARSET = "utf-8"
	# Create a new SES resource and specify a region.
	# client = sesClient()
	client = boto3.client('ses', region_name=AWS_REGION)
	# Create a multipart/mixed parent container.
	msg = MIMEMultipart('mixed')
	# Add subject, from and to lines.
	msg['Subject'] = SUBJECT
	msg['From'] = SENDER
	msg['To'] = RECIPIENT
	# Create a multipart/alternative child container.
	msg_body = MIMEMultipart('alternative')
	# Encode the text and HTML content and set the character encoding. This step is
	# necessary if you're sending a message with characters outside the ASCII range.
	textpart = MIMEText(BODY_TEXT.encode(CHARSET), 'plain', CHARSET)
	htmlpart = MIMEText(BODY_HTML.encode(CHARSET), 'html', CHARSET)
	# Add the text and HTML parts to the child container.
	msg_body.attach(textpart)
	msg_body.attach(htmlpart)
	# Define the attachment part and encode it using MIMEApplication.
	att = MIMEApplication(open(ATTACHMENT, 'rb').read())
	# Add a header to tell the email client to treat this part as an attachment,
	att.add_header('Content-Disposition', 'attachment', filename=os.path.basename(ATTACHMENT))
	msg.attach(msg_body)
	# Add the attachment to the parent container.
	msg.attach(att)
	try:
		# Provide the contents of the email.
		response = client.send_raw_email(
			Source=SENDER,
			Destinations=
			RECIPIENT.split(',')
			,
			RawMessage={
				'Data': msg.as_string(),
			},
			#	# ConfigurationSetName=CONFIGURATION_SET
		)
		Source = 'skondla@me.com',
		SourceArn = 'arn:aws:ses:us-east-1:1234567890:identity/skondla@me.com',
	# )
	# Display an error if something goes wrong.
	except ClientError as e:
		print(e.response['Error']['Message'])
	else:
		print("Email sent! Message ID:"),
		print(response['MessageId'])
