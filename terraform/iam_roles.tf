# IAM roles and policies for aws-cost-saver Lambda

resource "aws_iam_role" "cost_saver_lambda" {
  name = "aws-cost-saver-lambda-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

# Basic Lambda execution (logs)
resource "aws_iam_role_policy_attachment" "lambda_basic" {
  role       = aws_iam_role.cost_saver_lambda.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# Policy for RDS, EC2, ECS, ASG actions
resource "aws_iam_role_policy" "cost_saver_actions" {
  name   = "aws-cost-saver-actions"
  role   = aws_iam_role.cost_saver_lambda.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "RDS"
        Effect = "Allow"
        Action = [
          "rds:DescribeDBInstances",
          "rds:ListTagsForResource",
          "rds:StartDBInstance",
          "rds:StopDBInstance"
        ]
        Resource = "*"
      },
      {
        Sid    = "EC2"
        Effect = "Allow"
        Action = [
          "ec2:DescribeInstances",
          "ec2:DescribeTags",
          "ec2:StartInstances",
          "ec2:StopInstances"
        ]
        Resource = "*"
      },
      {
        Sid    = "ECS"
        Effect = "Allow"
        Action = [
          "ecs:DescribeServices",
          "ecs:ListServices",
          "ecs:UpdateService"
        ]
        Resource = "*"
      },
      {
        Sid    = "ASG"
        Effect = "Allow"
        Action = [
          "autoscaling:DescribeAutoScalingGroups",
          "autoscaling:UpdateAutoScalingGroup"
        ]
        Resource = "*"
      }
    ]
  })
}

# Optional: read config from S3
resource "aws_iam_role_policy" "cost_saver_s3_config" {
  count = var.config_s3_bucket != "" ? 1 : 0

  name   = "aws-cost-saver-s3-config"
  role   = aws_iam_role.cost_saver_lambda.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["s3:GetObject"]
        Resource = "arn:aws:s3:::${var.config_s3_bucket}/*"
      }
    ]
  })
}
