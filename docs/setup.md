# aws-cost-saver Setup Guide

## Prerequisites

- Python 3.12+
- AWS CLI configured (credentials and region)
- Terraform 1.0+ (optional, for Lambda + EventBridge)

## Installation

### Local / CLI

```bash
cd aws-cost-saver
python -m venv .venv
source .venv/bin/activate   # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
```

Run the CLI from the project root:

```bash
python cli/cost_saver.py stop-all dev --dry-run
python cli/cost_saver.py start-rds dev-database
```

### Install as command (optional)

```bash
pip install -e .
# Then: cost-saver stop-all dev --dry-run
```

Add a `pyproject.toml` or `setup.py` with entry point `cost-saver = cli.cost_saver:main` for this.

## Configuration

1. Copy or edit `config/environments.yaml`.
2. Define environments (e.g. `dev`, `staging`, `training`) and list:
   - **rds**: RDS instance identifiers
   - **ecs**: cluster name and list of service names
   - **ec2**: instance IDs or Name tag values
   - **asg**: Auto Scaling Group names
3. Set **schedule** (optional): `stop` and `start` times in 24h format (UTC).

Tag your AWS resources with `Environment=dev` (or your env name) to allow **resource discovery** in addition to explicit config.

## Safety

- **Production**: Resources tagged `Environment=production` (or `prod`) or `cost-saver=false` are never stopped automatically.
- Use `--force` only when you intentionally want to skip these checks (e.g. in a dedicated non-prod account).
- Always run with `--dry-run` first to preview actions.

## EventBridge + Lambda (Automation)

1. **Package the Lambda** (include dependencies):

   ```bash
   pip install -r requirements.txt -t package/
   cp -r cli core config scripts lambda_handler.py package/
   cd package && zip -r ../terraform/cost_saver_lambda.zip .
   cd ..
   ```

2. **Deploy with Terraform**:

   ```bash
   cd terraform
   terraform init
   terraform plan -var="environment_names=[\"dev\",\"staging\"]"
   terraform apply
   ```

3. EventBridge will trigger the Lambda at **07:00 UTC** (start) and **19:00 UTC** (stop). Set `COST_SAVER_ENVIRONMENTS` in the Lambda environment to a comma-separated list of env names, or rely on `config/environments.yaml` in the deployment package.

## Optional: Config in S3

Store `environments.yaml` in S3 and set Lambda env vars:

- `CONFIG_S3_BUCKET=your-bucket`
- `CONFIG_S3_KEY=config/environments.yaml`

Ensure the Lambda role has `s3:GetObject` on that bucket. The handler will download the config at runtime.

## Security Recommendations

- Use a dedicated IAM role for the Lambda with least-privilege (only RDS/EC2/ECS/ASG actions needed).
- Prefer running in a separate AWS account or OU for dev/staging only.
- Enable CloudWatch Logs and set log retention.
- Do not set `AWS_COST_SAVER_DISABLE_SAFETY=1` unless in a non-prod account and you accept the risk.
