locals {
  # lambda-sender is deployed as a ZIP package, not a container image
  # No ECR repository is needed for this function
  lambda_function_name = var.lambda_sender_name
}

