locals {
  lambda_sender_image_uri = "${aws_ecr_repository.lambda_sender_repo.repository_url}:${var.lambda_image_tag}"
}
