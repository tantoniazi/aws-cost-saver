# EventBridge rules for aws-cost-saver (standalone)
# Use with: terraform apply -var="lambda_function_arn=arn:aws:lambda:..."
# Or use terraform/ directory for full stack (Lambda + IAM + EventBridge).

variable "lambda_function_arn" {
  description = "ARN of the aws-cost-saver Lambda function to trigger"
  type        = string
}

# Start resources at 07:00 UTC every day
resource "aws_cloudwatch_event_rule" "cost_saver_start" {
  name                = "aws-cost-saver-start"
  description         = "Trigger cost-saver start action at 07:00 UTC"
  schedule_expression = "cron(0 7 * * ? *)"
}

resource "aws_cloudwatch_event_target" "cost_saver_start_lambda" {
  rule      = aws_cloudwatch_event_rule.cost_saver_start.name
  target_id = "CostSaverLambda"
  arn       = var.lambda_function_arn
  input     = jsonencode({ action = "start" })
}

# Stop resources at 19:00 UTC every day
resource "aws_cloudwatch_event_rule" "cost_saver_stop" {
  name                = "aws-cost-saver-stop"
  description         = "Trigger cost-saver stop action at 19:00 UTC"
  schedule_expression = "cron(0 19 * * ? *)"
}

resource "aws_cloudwatch_event_target" "cost_saver_stop_lambda" {
  rule      = aws_cloudwatch_event_rule.cost_saver_stop.name
  target_id = "CostSaverLambda"
  arn       = var.lambda_function_arn
  input     = jsonencode({ action = "stop" })
}
