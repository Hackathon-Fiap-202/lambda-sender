project_name        = "nextime-app"
aws_region          = "us-east-1"
account_id          = "383349724220"
package_type        = "Zip"
memory_size         = 256
timeout             = 60
lambda_image_tag    = "latest"
use_localstack      = false
localstack_endpoint = "http://localhost:4566"

ses_sender_email     = "framenextime@gmail.com"
cognito_user_pool_id = "us-east-1_f2c5af8d643640b39215421a484b9430"
