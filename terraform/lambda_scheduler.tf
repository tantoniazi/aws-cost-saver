# Lambda function for aws-cost-saver (scheduled execution)

# Bundle Lambda: run from repo root: pip install -r requirements.txt -t package/ && cp -r cli core config scripts lambda_handler.py package/ && cd package && zip -r ../terraform/cost_saver_lambda.zip .
# Or use the source_dir below and add a Lambda layer for PyYAML (see docs/setup.md).
data "archive_file" "cost_saver_zip" {
  type        = "zip"
  source_dir  = "${path.module}/../"
  output_path = "${path.module}/cost_saver_lambda.zip"
  exclude = [
    "terraform",
    ".git",
    "__pycache__",
    "*.pyc",
    "*.zip",
    "tests",
    ".pytest_cache",
    "venv",
    ".venv",
    "docs",
    ".cursor"
  ]
}

resource "aws_lambda_function" "cost_saver" {
  filename         = data.archive_file.cost_saver_zip.output_path
  function_name    = "aws-cost-saver"
  role             = aws_iam_role.cost_saver_lambda.arn
  handler          = "lambda_handler.handler"
  source_code_hash = data.archive_file.cost_saver_zip.output_base64sha256
  runtime          = "python3.12"
  timeout          = 300
  memory_size      = 256

  environment {
    variables = {
      AWS_COST_SAVER_LOG_LEVEL = "INFO"
      # In Lambda we rely on embedded config or S3; set to disable safety only if intended
      # AWS_COST_SAVER_DISABLE_SAFETY = "0"
      COST_SAVER_ENVIRONMENTS  = join(",", var.environment_names)
      CONFIG_S3_BUCKET         = var.config_s3_bucket
      CONFIG_S3_KEY            = var.config_s3_key
    }
  }
}

# CloudWatch Log Group (optional, Lambda creates by default)
resource "aws_cloudwatch_log_group" "cost_saver" {
  name              = "/aws/lambda/${aws_lambda_function.cost_saver.function_name}"
  retention_in_days = 14
}
