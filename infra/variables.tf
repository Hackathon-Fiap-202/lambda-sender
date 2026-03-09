# ==========================
# Configuração geral
# ==========================
variable "project_name" {
  description = "Nome do projeto ou aplicação principal (usado para prefixar recursos)."
  type        = string
}

variable "aws_region" {
  description = "Região da AWS onde os recursos serão criados."
  type        = string
  default     = "us-east-1"
}

variable "account_id" {
  description = "ID da conta AWS utilizada para o deploy dos recursos."
  type        = string
}

# ==========================
# Lambda Sender
# ==========================
variable "lambda_sender_name" {
  description = "Nome da função Lambda Sender."
  type        = string
  default     = "lambda-sender"
}

variable "lambda_image_tag" {
  description = "A tag da imagem Docker enviada para o ECR (ex: latest, v1.0.0) que as Lambdas devem usar."
  type        = string
  default     = "latest"
}

variable "package_type" {
  description = "Tipo de pacote da Lambda (ex: 'Zip' ou 'Image')."
  type        = string
  default     = "Image"
}

variable "memory_size" {
  description = "Quantidade de memória alocada (em MB) para a função Lambda."
  type        = number
  default     = 128
}

variable "timeout" {
  description = "Tempo máximo de execução da função Lambda, em segundos."
  type        = number
  default     = 30
}

variable "ses_sender_email" {
  description = "E-mail verificado no SES para envio de notificações."
  type        = string
}

variable "cognito_user_pool_id" {
  description = "ID do User Pool do Cognito para buscar emails de usuários."
  type        = string
}

