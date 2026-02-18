import json
import os
import boto3
import logging
from botocore.exceptions import ClientError

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize clients outside the handler for execution environment reuse
cognito_client = boto3.client('cognito-idp')
ses_client = boto3.client('ses')

# Environment variables
USER_POOL_ID = os.environ.get('USER_POOL_ID')
SOURCE_EMAIL = os.environ.get('SOURCE_EMAIL')

def get_user_email(user_id):
    """
    Retrieves the user's email from Cognito using the user_id.
    """
    try:
        response = cognito_client.admin_get_user(
            UserPoolId=USER_POOL_ID,
            Username=user_id
        )
        
        for attribute in response.get('UserAttributes', []):
            if attribute['Name'] == 'email':
                return attribute['Value']
        
        logger.warning(f"Email attribute not found for user: {user_id}")
        return None

    except ClientError as e:
        logger.error(f"Error getting user {user_id} from Cognito: {e}")
        # Depending on the requirement, we might want to raise this or handle it gracefully.
        # For a batch process like SQS, raising it might cause the whole batch to fail 
        # or the message to go back to the queue (if not handled).
        # Here we will log and return None to skip processing for this user.
        return None

def send_email_notification(recipient_email):
    """
    Sends an email notification via SES.
    """
    try:
        response = ses_client.send_email(
            Source=SOURCE_EMAIL,
            Destination={
                'ToAddresses': [recipient_email]
            },
            Message={
                'Subject': {
                    'Data': 'Video Processing Complete',
                    'Charset': 'UTF-8'
                },
                'Body': {
                    'Text': {
                        'Data': 'Your video has been successfully processed and is ready for download.',
                        'Charset': 'UTF-8'
                    },
                    'Html': {
                        'Data': '<html><body><h1>Video Processed</h1><p>Your video has been successfully processed and is ready for download.</p></body></html>',
                        'Charset': 'UTF-8'
                    }
                }
            }
        )
        logger.info(f"Email sent to {recipient_email}. MessageId: {response['MessageId']}")
        return True

    except ClientError as e:
        logger.error(f"Error sending email to {recipient_email}: {e}")
        return False

def lambda_handler(event, context):
    """
    Lambda handler for processing SQS messages.
    """
    if not USER_POOL_ID or not SOURCE_EMAIL:
        logger.error("Environment variables USER_POOL_ID and SOURCE_EMAIL must be set.")
        return {
            'statusCode': 500,
            'body': json.dumps('Configuration Error')
        }

    logger.info(f"Received event: {json.dumps(event)}")
    
    # Iterate through records (handling batch processing)
    if 'Records' in event:
        for record in event['Records']:
            try:
                body = json.loads(record['body'])
                user_id = body.get('cognito_user_id')
                
                if not user_id:
                    logger.warning(f"No cognito_user_id found in message body: {record['body']}")
                    continue
                
                logger.info(f"Processing video completion for user: {user_id}")
                
                email = get_user_email(user_id)
                
                if email:
                    success = send_email_notification(email)
                    if success:
                        logger.info(f"Successfully processed message for user: {user_id}")
                    else:
                        logger.error(f"Failed to send email for user: {user_id}")
                else:
                    logger.warning(f"Could not retrieve email for user: {user_id}")

            except json.JSONDecodeError:
                logger.error(f"Failed to decode message body: {record['body']}")
            except Exception as e:
                logger.error(f"Unexpected error processing record: {e}")
                # We might want to raise here to trigger DLQ or retry logic if appropriate
                
    return {
        'statusCode': 200,
        'body': json.dumps('Processing Complete')
    }
