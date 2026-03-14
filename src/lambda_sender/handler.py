import json
import os
import boto3
import logging
from botocore.exceptions import ClientError

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Environment variables
USER_POOL_ID = os.environ.get('COGNITO_USER_POOL_ID')
SOURCE_EMAIL = os.environ.get('SES_SENDER_EMAIL')
ENDPOINT_URL = os.environ.get('AWS_ENDPOINT_URL')

cognito_client = boto3.client('cognito-idp', endpoint_url=ENDPOINT_URL)
ses_client = boto3.client('ses', endpoint_url=ENDPOINT_URL)

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
        return None
    except Exception as e:
        logger.error(f"Unexpected error getting user from Cognito: {e}")
        return None

def send_email_notification(recipient_email, key_name=None, status=None, download_url=None):  # adiciona
    status_display = status if status else 'completed'
    key_name_display = key_name if key_name else 'your file'

    subject = f'Video Processing {status_display.capitalize()}'

    text_body = f'Your video "{key_name_display}" has been {status_display}.'
    if download_url:
        text_body += f' Download it here: {download_url}'
    elif status and status.lower() == 'completed':
        text_body += ' It is ready for download.'

    html_body = f'''<html>
    <body>
    <h1>Video Processing {status_display.capitalize()}</h1>
    <p><strong>File:</strong> {key_name_display}</p>
    <p><strong>Status:</strong> {status_display}</p>
    <p>Your video has been {status_display}.</p>
    {f'<p><a href="{download_url}">Click here to download your video</a></p>' if download_url else
    '<p>It is ready for download.</p>' if status and status.lower() == 'completed' else ''}
    </body>
    </html>'''

    try:
        response = ses_client.send_email(
            Source=SOURCE_EMAIL,
            Destination={'ToAddresses': [recipient_email]},
            Message={
                'Subject': {'Data': subject, 'Charset': 'UTF-8'},
                'Body': {
                    'Text': {'Data': text_body, 'Charset': 'UTF-8'},
                    'Html': {'Data': html_body, 'Charset': 'UTF-8'}
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

    print(f"DEBUG: Internal lambda-sender invoked with event: {json.dumps(event)}")
    logger.info(f"Received event: {json.dumps(event)}")
    
    # Iterate through records (handling batch processing)
    if 'Records' in event:
        for record in event['Records']:
            try:
                body = json.loads(record['body'])
                user_id = body.get('cognito_user_id')
                key_name = body.get('key_name')
                status = body.get('status')
                download_url = body.get('download_url')
                
                if not user_id:
                    logger.warning(f"No cognito_user_id found in message body: {record['body']}")
                    continue
                
                # Validate key_name and status are strings
                if key_name and not isinstance(key_name, str):
                    logger.warning(f"key_name is not a string: {key_name}")
                    key_name = None
                
                if status and not isinstance(status, str):
                    logger.warning(f"status is not a string: {status}")
                    status = None

                if download_url and not isinstance(download_url, str):
                    logger.warning(f"download_url is not a string: {download_url}")
                    download_url = None

                if status and status.upper() == 'PROCESSING':
                    logger.info(f"Skipping email notification for PROCESSING status, user: {user_id}")
                    continue

                if not key_name:
                    logger.warning(f"No key_name found in message body for user: {user_id}")
                
                if not status:
                    logger.warning(f"No status found in message body for user: {user_id}")
                
                logger.info(f"Processing video completion for user: {user_id}, file: {key_name}, status: {status}")
                
                email = get_user_email(user_id)
                
                if email:
                    success = send_email_notification(email, key_name, status, download_url)
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
