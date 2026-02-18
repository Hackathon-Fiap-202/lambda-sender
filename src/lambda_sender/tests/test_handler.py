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
                    'body': json.dumps({'cognito_user_id': 'user123'})
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

if __name__ == '__main__':
    unittest.main()
