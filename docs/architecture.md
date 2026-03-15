# aws-cost-saver Architecture

## Overview

aws-cost-saver reduces AWS costs by stopping, starting, and resizing resources on a schedule. It targets development, staging, and training environments to achieve an estimated **60–80% cost reduction** for those workloads.

## Components

### 1. Configuration (`config/environments.yaml`)

- **Per-environment** definition of RDS, ECS, EC2, and ASG resources.
- **Schedule** (start/stop times in UTC) used by the scheduler engine and EventBridge.
- Optional **default** section for shared schedule and defaults.

### 2. Core Modules (`core/`)

- **aws_clients.py**: boto3 client factory (RDS, ECS, EC2, Auto Scaling) with region/profile support.
- **resource_discovery.py**: Finds resources by tags (e.g. `Environment=dev`) and by config lists.
- **scheduler_engine.py**: Loads YAML config, resolves environment and resource lists, exposes schedule.
- **safety_checks.py**: Ensures we never auto-stop production or resources tagged `cost-saver=false`.
- **logging_config.py**: Structured JSON logging (resource, action, status, timestamp).
- **cost_estimation.py**: Simple hourly-rate based savings estimation.

### 3. Scripts (`scripts/`)

Single-resource actions, usable from CLI and Lambda:

- **stop_rds.py** / **start_rds.py**: RDS instance stop/start.
- **stop_ec2.py** / **start_ec2.py**: EC2 instance stop/start.
- **resize_ecs.py**: ECS service desired count (e.g. 0 at night).
- **scale_asg.py**: ASG min/max/desired capacity.

All support `--dry-run`, `--force`, `--region`, `--profile`.

### 4. CLI (`cli/cost_saver.py`)

- **stop-rds**, **start-rds**, **stop-ec2**, **start-ec2**, **resize-ecs**, **scale-asg**: Single-resource commands.
- **stop-all**, **start-all**: Act on all resources for an environment (from config + discovery).
- **schedule-run**: Entrypoint for automation (e.g. Lambda) with `--action start|stop` and `--env`.
- **estimate**: Prints estimated savings for an environment.

### 5. Scheduler / EventBridge

- **scheduler/eventbridge_rules.tf**: Standalone Terraform rules; target Lambda via `lambda_function_arn` variable.
- **scheduler/eventbridge.json**: Reference for manual EventBridge setup (cron expressions and target input).

Typical rules:

- **Start**: `cron(0 7 * * ? *)` (07:00 UTC).
- **Stop**: `cron(0 19 * * ? *)` (19:00 UTC).

### 6. Lambda (`lambda_handler.py`)

- **Handler**: Reads `event.action` (`start` or `stop`) and optional `event.environments`.
- **Environments**: From event or env var `COST_SAVER_ENVIRONMENTS` (comma-separated).
- **Config**: Bundled `config/environments.yaml` or downloaded from S3 (`CONFIG_S3_BUCKET` / `CONFIG_S3_KEY`).
- **Actions**: Calls the same logic as the CLI (`cmd_start_all` / `cmd_stop_all`) so behavior is identical.

### 7. Terraform (`terraform/`)

- **main.tf**: Provider and variables (region, environment list, optional S3 config).
- **iam_roles.tf**: Lambda execution role and policy for RDS, EC2, ECS, ASG (and optional S3 config).
- **lambda_scheduler.tf**: Lambda function (Python 3.12), zip from project root (see setup.md for packaging).
- **eventbridge.tf**: EventBridge rules and targets, Lambda permissions.

## Data Flow

1. **Manual/CLI**: User runs `cost-saver stop-all dev --dry-run` → scheduler_engine loads config → resources resolved (config + discovery) → safety_checks → scripts perform stop.
2. **Scheduled**: EventBridge fires at 07:00/19:00 → Lambda invoked with `{ "action": "start" }` or `{ "action": "stop" }` → handler loads config and env list → same stop-all/start-all logic as CLI.

## Safety Guarantees

- **Production**: `Environment=production` or `prod` → no stop.
- **Opt-out**: Tag `cost-saver=false` → no stop.
- **Override**: `--force` (CLI) or `AWS_COST_SAVER_DISABLE_SAFETY=1` (Lambda) skips checks; use only in non-prod.

## Monitoring and Cost Estimation

- **Logging**: JSON logs with resource, action, status, timestamp (and optional CloudWatch).
- **Estimate**: `cost-saver estimate dev --hours 12` uses built-in hourly rates to print estimated savings.
- For production metrics, integrate with **AWS Cost Explorer** or **CloudWatch custom metrics** (resources stopped, estimated cost saved).
