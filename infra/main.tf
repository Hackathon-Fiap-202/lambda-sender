# ==========================
# Lambda Sender Archive
# ==========================
data "archive_file" "lambda_sender" {
  type        = "zip"
  source_file = "${path.module}/../lambda-handler.zip"
  output_path = "${path.module}/.terraform/lambda-handler-archive.zip"
}

# ==========================
# IAM Role for Lambda Sender
# ==========================
module "lambda_sender_role" {
  source    = "./modules/iam/roles"
  role_name = "LambdaSenderRole"
}

module "lambda_sender_policy" {
  source      = "./modules/iam/policies"
  policy_name = "LambdaSenderPolicy"
  description = "Permissions for Lambda Sender"
  policy_document = {
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "sqs:ReceiveMessage",
          "sqs:DeleteMessage",
          "sqs:GetQueueAttributes"
        ]
        Resource = data.aws_sqs_queue.video_processed_queue.arn
      },
      {
        Effect = "Allow"
        Action = [
          "ses:SendEmail",
          "ses:SendRawEmail"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "cognito-idp:AdminGetUser"
        ]
        Resource = "arn:aws:cognito-idp:${var.aws_region}:${var.account_id}:userpool/${var.cognito_user_pool_id}"
      }
    ]
  }
}

resource "aws_iam_role_policy_attachment" "attach_lambda_sender" {
  role       = module.lambda_sender_role.role_name
  policy_arn = module.lambda_sender_policy.policy_arn
}

# ==========================
# Lambda Function
# ==========================
resource "aws_lambda_function" "lambda_sender" {
  function_name = var.lambda_sender_name
  role          = module.lambda_sender_role.role_arn
  handler       = "lambda_sender.handler.handler"
  runtime       = "python3.11"

  # Use local ZIP file instead of ECR image
  filename         = data.archive_file.lambda_sender.output_path
  source_code_hash = data.archive_file.lambda_sender.output_base64sha256

  timeout     = var.timeout
  memory_size = var.memory_size

  environment {
    variables = {
      SES_SENDER_EMAIL     = var.ses_sender_email
      COGNITO_USER_POOL_ID = var.cognito_user_pool_id
      REGION               = var.aws_region
      USE_LOCALSTACK       = var.use_localstack ? "true" : "false"
      LOCALSTACK_ENDPOINT  = var.localstack_endpoint
    }
  }

  depends_on = [
    module.lambda_sender_role
  ]
}

# ==========================
# SQS Trigger
# ==========================
resource "aws_lambda_event_source_mapping" "sqs_trigger" {
  event_source_arn = data.aws_sqs_queue.video_processed_queue.arn
  function_name    = aws_lambda_function.lambda_sender.arn
  batch_size       = 10
  enabled          = true
}


