# ==========================
# ECR Repository
# ==========================
resource "aws_ecr_repository" "lambda_sender" {
  name                 = local.lambda_sender_ecr_name
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }
}

resource "aws_ecr_lifecycle_policy" "lambda_sender" {
  repository = aws_ecr_repository.lambda_sender.name

  policy = jsonencode({
    rules = [{
      rulePriority = 1
      description  = "Keep last 10 images"
      selection = {
        tagStatus   = "any"
        countType   = "imageCountMoreThan"
        countNumber = 10
      }
      action = { type = "expire" }
    }]
  })
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
# Lambda Function (ECR image)
# ==========================
resource "aws_lambda_function" "lambda_sender" {
  function_name = var.lambda_sender_name
  role          = module.lambda_sender_role.role_arn
  package_type  = "Image"
  image_uri     = "${local.lambda_sender_ecr_uri}:${var.lambda_image_tag}"

  timeout     = var.timeout
  memory_size = var.memory_size

  environment {
    variables = {
      SES_SENDER_EMAIL     = var.ses_sender_email
      COGNITO_USER_POOL_ID = var.cognito_user_pool_id
      REGION               = var.aws_region
    }
  }

  depends_on = [
    module.lambda_sender_role,
    aws_ecr_repository.lambda_sender,
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
