# lambda-sender

Lambda de notificação por e-mail do projeto **nexTime-frame**. Ao receber uma mensagem na fila SQS `video-processed-event`, a função recupera o e-mail do usuário no Cognito e envia uma notificação via SES informando o resultado do processamento de vídeo.

## Sumário

- [Visão Geral](#visão-geral)
- [Arquitetura](#arquitetura)
- [Fluxo de Execução](#fluxo-de-execução)
- [Recursos Provisionados](#recursos-provisionados)
- [Pré-requisitos](#pré-requisitos)
- [Variáveis de Ambiente](#variáveis-de-ambiente)
- [Desenvolvimento Local](#desenvolvimento-local)
- [Build e Deploy](#build-e-deploy)
- [CI/CD](#cicd)
- [Ordem de Deploy](#ordem-de-deploy)
- [Contribuição](#contribuição)

---

## Visão Geral

A `lambda-sender` é o **quinto e último stack a ser implantado**. É empacotada como imagem Docker (Python 3.12) e publicada em um repositório ECR dedicado. O trigger é um **event source mapping** SQS com batch size 10.

---

## Arquitetura

```
SQS: video-processed-event
      │  (batch size 10, trigger automático)
      ▼
Lambda: lambda-sender  (Python 3.12, Docker)
      │
      ├── Cognito AdminGetUser  ──► obtém e-mail do usuário pelo cognito_user_id
      │
      └── SES SendEmail  ──► envia e-mail HTML + texto ao usuário
```

---

## Fluxo de Execução

1. O `ms-video` publica uma mensagem em `video-processed-event` com o corpo:
   ```json
   {
     "cognito_user_id": "<sub do usuário no Cognito>",
     "key_name": "<uuid>.zip",
     "status": "COMPLETED"
   }
   ```
2. O event source mapping dispara a Lambda com até 10 registros por invocação
3. Para cada registro, a Lambda:
   - Extrai `cognito_user_id`, `key_name` e `status` do corpo da mensagem
   - Chama `AdminGetUser` no Cognito User Pool para obter o e-mail do usuário
   - Envia um e-mail HTML e texto via SES usando o remetente `SES_SENDER_EMAIL`
4. Em caso de erro, a mensagem permanece na fila (sem DLQ configurada)

---

## Recursos Provisionados

A infraestrutura (`infra/`) é gerenciada com Terraform:

| Recurso | Descrição |
|---|---|
| `aws_ecr_repository` | Repositório ECR `lambda-sender` para armazenar a imagem Docker |
| `aws_lambda_function` | Função Lambda com runtime `FROM_IMAGE`, memória e timeout configuráveis |
| `aws_lambda_event_source_mapping` | Trigger SQS na fila `video-processed-event`, batch size 10 |
| `aws_iam_role` + políticas | Permissões: `cognito-idp:AdminGetUser`, `ses:SendEmail`, `sqs:ReceiveMessage`, `sqs:DeleteMessage`, `logs:*` |

---

## Pré-requisitos

- [Python 3.12](https://www.python.org/downloads/)
- [Docker](https://www.docker.com/products/docker-desktop)
- [Terraform](https://developer.hashicorp.com/terraform/downloads) >= 1.0
- [AWS CLI](https://aws.amazon.com/cli/) configurado
- Estado remoto do `infra-gateway` disponível (para `cognito_user_pool_id`)
- Identidade SES verificada (provisionada pelo `infra-messaging`)

---

## Variáveis de Ambiente

Injetadas na Lambda via Terraform:

| Variável | Descrição | Origem |
|---|---|---|
| `COGNITO_USER_POOL_ID` | ID do Cognito User Pool | Output remoto do `infra-gateway` |
| `SES_SENDER_EMAIL` | E-mail remetente verificado no SES | Variável Terraform (`ses_sender_email`) |
| `REGION` | Região AWS | Variável Terraform (`region`) |

---

## Desenvolvimento Local

O handler está em `src/lambda_sender/handler.py` e as dependências em `src/lambda_sender/requirements.txt`:

```
boto3
botocore
```

Para testar localmente com um payload simulado:

```bash
cd src/lambda_sender

# Instalar dependências
pip install -r requirements.txt

# Simular invocação (requer credenciais AWS configuradas localmente)
python -c "
import json, handler
event = {
  'Records': [{
    'body': json.dumps({
      'cognito_user_id': 'user-sub-uuid',
      'key_name': 'meu-video.zip',
      'status': 'COMPLETED'
    })
  }]
}
handler.handler(event, None)
"
```

---

## Build e Deploy

O deploy segue duas fases:

### Fase 1 — Bootstrap do ECR (apenas no primeiro deploy)

```bash
cd lambda-sender/infra
terraform init
terraform apply -target=aws_ecr_repository.lambda_sender
```

### Fase 2 — Build da imagem, push e deploy completo

```bash
# Build da imagem Docker
docker build -t lambda-sender:$GITHUB_SHA .

# Autenticar no ECR
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin \
  $AWS_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com

# Tag e push
docker tag lambda-sender:$GITHUB_SHA \
  $AWS_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/lambda-sender:$GITHUB_SHA
docker push $AWS_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/lambda-sender:$GITHUB_SHA

# Apply Terraform com a nova tag de imagem
cd infra
terraform apply -auto-approve \
  -var="lambda_image_tag=$GITHUB_SHA"
```

---

## CI/CD

O pipeline `.github/workflows/deploy.yml` é acionado em push para `main`.

| Etapa | Descrição |
|---|---|
| Configure AWS | OIDC via `AWS_ROLE_ARN` |
| Terraform Init | Inicializa o backend S3 |
| ECR Bootstrap | `terraform apply -target=aws_ecr_repository.lambda_sender` |
| Docker Build & Push | Build da imagem com tag `$GITHUB_SHA` e push para ECR |
| Terraform Apply | Deploy completo com `-var="lambda_image_tag=$GITHUB_SHA"` |

**Data source remoto consumido:**

| Stack | Bucket Key | Dado utilizado |
|---|---|---|
| `infra-gateway` | `infra-gateway/infra.tfstate` | `cognito_user_pool_id` |

**Secrets do GitHub necessários:**

| Secret | Descrição |
|---|---|
| `AWS_ACCOUNT_ID` | ID da conta AWS |
| `AWS_ROLE_ARN` | ARN da role com permissões de deploy |

---

## Backend Remoto

```hcl
backend "s3" {
  bucket  = "nextime-frame-state-bucket-s3"
  key     = "lambda-sender/infra.tfstate"
  region  = "us-east-1"
  encrypt = true
}
```

---

## Ordem de Deploy

```
1. infra-core
2. infra-messaging
3. infra-gateway
4. Infra-ecs
5. lambda-sender       ← este repositório
```

---

## Estrutura do Projeto

```
lambda-sender/
├── src/
│   └── lambda_sender/
│       ├── handler.py           # Handler principal: lê SQS → Cognito → SES
│       └── requirements.txt     # boto3, botocore
├── Dockerfile                   # Imagem Python 3.12 para Lambda container
├── infra/
│   ├── main.tf                  # Lambda, event source mapping SQS
│   ├── variables.tf             # Declaração de variáveis
│   ├── locals.tf                # Locals (ex.: URL da imagem ECR)
│   ├── data.tf                  # Remote state do infra-gateway
│   └── providers.tf             # Provider AWS + backend S3
└── README.md
```

---

## Contribuição

Este repositório faz parte do hackathon FIAP — nexTime-frame. Siga o padrão de commits convencional (`feat:`, `fix:`, `docs:`, `chore:`) e mantenha a estrutura modular.
