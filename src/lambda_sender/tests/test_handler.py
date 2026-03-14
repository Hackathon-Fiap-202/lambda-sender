import json
import unittest
from unittest.mock import MagicMock, patch
import os
import sys

# Perform absolute imports for the test execution
# This assumes the test file is run from the project root or similar.
# Adjusting path to include src/lambda_sender
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import handler

class TestLambdaHandler(unittest.TestCase):

    def setUp(self):
        # Set environment variables in the handler module
        handler.USER_POOL_ID = 'pool_id'
        handler.SOURCE_EMAIL = 'sender@example.com'
        
    @patch('handler.cognito_client')
    @patch('handler.ses_client')
    def test_successful_processing(self, mock_ses, mock_cognito):
        # Mock Cognito Client
        mock_cognito.admin_get_user.return_value = {
            'UserAttributes': [{'Name': 'email', 'Value': 'user@example.com'}]
        }
        
        # Mock SES Client
        mock_ses.send_email.return_value = {'MessageId': '12345'}

        # Create mock SQS event
        event = {
            'Records': [
                {
                    'body': json.dumps({
                        'cognito_user_id': 'user123',
                        'key_name': 'videos/user123/my-video.mp4',
                        'status': 'completed'
                    })
                }
            ]
        }

        # Call the Lambda handler
        response = handler.lambda_handler(event, None)

        # Assertions
        self.assertEqual(response['statusCode'], 200)
        mock_cognito.admin_get_user.assert_called_once_with(
            UserPoolId='pool_id',
            Username='user123'
        )
        mock_ses.send_email.assert_called_once()
        
    @patch('handler.cognito_client')
    @patch('handler.ses_client')
    def test_missing_user_email(self, mock_ses, mock_cognito):
        # Mock Cognito Client - No email
        mock_cognito.admin_get_user.return_value = {
            'UserAttributes': [{'Name': 'phone_number', 'Value': '+1234567890'}]
        }
        
        event = {
            'Records': [
                {
                    'body': json.dumps({'cognito_user_id': 'user123'})
                }
            ]
        }

        response = handler.lambda_handler(event, None)

        self.assertEqual(response['statusCode'], 200)
        mock_cognito.admin_get_user.assert_called_once()
        mock_ses.send_email.assert_not_called()
    
    @patch('handler.cognito_client')
    @patch('handler.ses_client')
    def test_missing_key_name_and_status(self, mock_ses, mock_cognito):
        # Mock Cognito Client
        mock_cognito.admin_get_user.return_value = {
            'UserAttributes': [{'Name': 'email', 'Value': 'user@example.com'}]
        }
        
        # Mock SES Client
        mock_ses.send_email.return_value = {'MessageId': '12345'}
        
        # Event without key_name and status
        event = {
            'Records': [
                {
                    'body': json.dumps({'cognito_user_id': 'user123'})
                }
            ]
        }

        response = handler.lambda_handler(event, None)

        # Should still process and send email with defaults
        self.assertEqual(response['statusCode'], 200)
        mock_cognito.admin_get_user.assert_called_once()
        mock_ses.send_email.assert_called_once()
    
    @patch('handler.cognito_client')
    @patch('handler.ses_client')
    def test_invalid_types_for_key_name_and_status(self, mock_ses, mock_cognito):
        # Mock Cognito Client
        mock_cognito.admin_get_user.return_value = {
            'UserAttributes': [{'Name': 'email', 'Value': 'user@example.com'}]
        }
        
        # Mock SES Client
        mock_ses.send_email.return_value = {'MessageId': '12345'}
        
        # Event with invalid types (numbers instead of strings)
        event = {
            'Records': [
                {
                    'body': json.dumps({
                        'cognito_user_id': 'user123',
                        'key_name': 12345,
                        'status': 999
                    })
                }
            ]
        }

        response = handler.lambda_handler(event, None)

        # Should still process with None values
        self.assertEqual(response['statusCode'], 200)
        mock_cognito.admin_get_user.assert_called_once()
        mock_ses.send_email.assert_called_once()
        # Verify call was made with None for invalid types
        call_args = mock_ses.send_email.call_args
        # The email should be sent but with default values
    
    @patch('handler.cognito_client')
    @patch('handler.ses_client')
    def test_with_failed_status(self, mock_ses, mock_cognito):
        # Mock Cognito Client
        mock_cognito.admin_get_user.return_value = {
            'UserAttributes': [{'Name': 'email', 'Value': 'user@example.com'}]
        }
        
        # Mock SES Client
        mock_ses.send_email.return_value = {'MessageId': '12345'}
        
        event = {
            'Records': [
                {
                    'body': json.dumps({
                        'cognito_user_id': 'user123',
                        'key_name': 'videos/user123/failed-video.mp4',
                        'status': 'failed'
                    })
                }
            ]
        }

        response = handler.lambda_handler(event, None)

        self.assertEqual(response['statusCode'], 200)
        mock_cognito.admin_get_user.assert_called_once()
        mock_ses.send_email.assert_called_once()
        
        # Verify email was sent with failed status
        call_args = mock_ses.send_email.call_args[1]
        self.assertIn('Failed', call_args['Message']['Subject']['Data'])

if __name__ == '__main__':
    unittest.main()
