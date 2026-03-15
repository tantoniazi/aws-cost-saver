# EventBridge rules to trigger cost-saver Lambda

resource "aws_cloudwatch_event_rule" "cost_saver_start" {
  name                = "aws-cost-saver-start"
  description         = "Trigger cost-saver start at 07:00 UTC"
  schedule_expression  = "cron(0 7 * * ? *)"
}

resource "aws_cloudwatch_event_target" "cost_saver_start" {
  rule      = aws_cloudwatch_event_rule.cost_saver_start.name
  target_id = "CostSaverLambda"
  arn       = aws_lambda_function.cost_saver.arn
  input     = jsonencode({ action = "start" })
}

resource "aws_cloudwatch_event_rule" "cost_saver_stop" {
  name                = "aws-cost-saver-stop"
  description         = "Trigger cost-saver stop at 19:00 UTC"
  schedule_expression = "cron(0 19 * * ? *)"
}

resource "aws_cloudwatch_event_target" "cost_saver_stop" {
  rule      = aws_cloudwatch_event_rule.cost_saver_stop.name
  target_id = "CostSaverLambda"
  arn       = aws_lambda_function.cost_saver.arn
  input     = jsonencode({ action = "stop" })
}

resource "aws_lambda_permission" "eventbridge_start" {
  statement_id  = "AllowExecutionFromEventBridgeStart"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.cost_saver.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.cost_saver_start.arn
}

resource "aws_lambda_permission" "eventbridge_stop" {
  statement_id  = "AllowExecutionFromEventBridgeStop"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.cost_saver.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.cost_saver_stop.arn
}
