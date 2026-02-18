#!/bin/bash
echo "Initializing LocalStack resources..."

# Create SQS Queue
awslocal sqs create-queue --queue-name video-processed-queue

# Create ECR Repository (optional, if you want it pre-created)
awslocal ecr create-repository --repository-name lambda-sender-repo

echo "LocalStack resources initialized!"
