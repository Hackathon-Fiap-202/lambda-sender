data "aws_caller_identity" "current" {}

data "aws_sqs_queue" "video_processed_queue" {
  name = "video-processed-event"
}

# Read Cognito user pool ID from infra-gateway remote state
# Eliminates the need to hardcode cognito_user_pool_id in terraform.tfvars
data "terraform_remote_state" "infra_gateway" {
  backend = "s3"
  config = {
    bucket = "nextime-frame-state-bucket"
    key    = "infra-gateway/infra.tfstate"
    region = "us-east-1"
  }
}

