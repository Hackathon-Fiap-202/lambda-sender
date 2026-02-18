output "ecr_lambda_sender_url" {
  description = "URL do ECR da Lambda Sender"
  value       = aws_ecr_repository.lambda_sender_repo.repository_url
}

output "lambda_sender_function_name" {
  value = aws_lambda_function.lambda_sender.function_name
}

output "lambda_sender_invoke_arn" {
  value = aws_lambda_function.lambda_sender.invoke_arn
}

output "lambda_sender_arn" {
  value = aws_lambda_function.lambda_sender.arn
}

output "sqs_video_processed_url" {
  value = data.aws_sqs_queue.video_processed_queue.url
}

output "sqs_video_processed_arn" {
  value = data.aws_sqs_queue.video_processed_queue.arn
}
