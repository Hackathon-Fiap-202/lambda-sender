locals {
  lambda_function_name   = var.lambda_sender_name
  lambda_sender_ecr_name = "lambda-sender"
  account_id             = data.aws_caller_identity.current.account_id
  lambda_sender_ecr_uri  = "${local.account_id}.dkr.ecr.${var.aws_region}.amazonaws.com/${local.lambda_sender_ecr_name}"
  cognito_user_pool_id   = data.terraform_remote_state.infra_gateway.outputs.cognito_user_pool_id
}
