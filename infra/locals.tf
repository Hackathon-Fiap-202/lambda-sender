locals {
  lambda_function_name   = var.lambda_sender_name
  lambda_sender_ecr_name = "lambda-sender"
  lambda_sender_ecr_uri  = "${var.account_id}.dkr.ecr.${var.aws_region}.amazonaws.com/${local.lambda_sender_ecr_name}"
}
