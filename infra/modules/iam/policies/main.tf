resource "aws_iam_policy" "this" {
  name        = var.policy_name
  description = var.description
  policy      = jsonencode(var.policy_document)
}

output "policy_arn" {
  value = aws_iam_policy.this.arn
}
