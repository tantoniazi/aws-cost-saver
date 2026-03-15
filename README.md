# aws-cost-saver

**Production-grade infrastructure automation to reduce AWS costs** by stopping, starting, and resizing resources on a schedule. Designed to cut **development, staging, and training environment costs by 60–80%**.

The toolkit is **safe** (production and opted-out resources are never auto-stopped), **configurable** (YAML + tags), and **automation-friendly** (CLI + EventBridge/Lambda).

---

## Features

- **Stop / Start RDS** instances
- **Stop / Start EC2** instances  
- **Resize ECS** services (e.g. scale to 0 at night)
- **Scale Auto Scaling Groups** (min, max, desired)
- **Resource discovery** by tag (`Environment=dev`)
- **Safety checks**: no automatic stop for `Environment=production` or `cost-saver=false`
- **Dry-run mode** to preview actions
- **EventBridge + Lambda** for fully automated schedules
- **Structured JSON logging** and optional cost estimation

---

## Tech Stack

- **Python 3.12**, **boto3**, **PyYAML**
- **AWS EventBridge** (cron rules)
- **AWS Lambda** (optional execution mode)
- **Terraform** (optional): Lambda, IAM, EventBridge

Runs **locally via CLI** or **automatically via EventBridge/Lambda**.

---

## Repository Structure

```
aws-cost-saver/
├── cli/
│   └── cost_saver.py          # Main CLI entrypoint
├── config/
│   └── environments.yaml     # Per-environment resource and schedule config
├── core/
│   ├── aws_clients.py        # boto3 client factory
│   ├── resource_discovery.py  # Find resources by tag/config
│   ├── scheduler_engine.py    # Config loader and schedule logic
│   ├── safety_checks.py       # Production and opt-out guards
│   ├── logging_config.py      # JSON logging
│   └── cost_estimation.py     # Simple savings estimation
├── scripts/
│   ├── start_rds.py / stop_rds.py
│   ├── start_ec2.py / stop_ec2.py
│   ├── resize_ecs.py
│   └── scale_asg.py
├── scheduler/
│   ├── eventbridge_rules.tf   # Standalone EventBridge rules (Terraform)
│   └── eventbridge.json       # Reference for manual EventBridge setup
├── terraform/
│   ├── main.tf
│   ├── iam_roles.tf
│   ├── lambda_scheduler.tf
│   └── eventbridge.tf
├── docs/
│   ├── setup.md
│   └── architecture.md
├── tests/
├── lambda_handler.py         # Lambda entrypoint
├── requirements.txt
├── pyproject.toml
└── README.md
```

---

## Installation

```bash
git clone <repo>
cd aws-cost-saver
python3.12 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Optional: install as CLI command:

```bash
pip install -e .
cost-saver --help
```

---

## Configuration

Edit `config/environments.yaml`:

```yaml
dev:
  rds:
    - dev-database
  ecs:
    cluster: dev-cluster
    services:
      - api
      - workers
  ec2:
    - dev-runner
    - dev-bastion
  asg: []
  schedule:
    stop: "19:00"   # UTC
    start: "07:00"
```

- **rds**: RDS instance identifiers  
- **ecs**: cluster name + list of service names  
- **ec2**: instance IDs or Name tag values  
- **asg**: Auto Scaling Group names  
- **schedule**: used by EventBridge/scheduler (stop/start times in UTC)

Tag resources with `Environment=dev` to allow **resource discovery** in addition to explicit lists.

---

## CLI Usage

From project root (with venv activated):

```bash
# Single resources
python cli/cost_saver.py stop-rds dev-database
python cli/cost_saver.py start-rds dev-database
python cli/cost_saver.py stop-ec2 i-12345678
python cli/cost_saver.py start-ec2 i-12345678
python cli/cost_saver.py resize-ecs dev-cluster api 0
python cli/cost_saver.py scale-asg my-asg 0 --min 0 --max 0

# Environment-wide
python cli/cost_saver.py stop-all dev --dry-run
python cli/cost_saver.py start-all dev
python cli/cost_saver.py schedule-run --env dev --action stop

# Cost estimation
python cli/cost_saver.py estimate dev --hours 12
```

Global options: `--config`, `--region`, `--profile`, `--dry-run`, `--force`.

---

## Safety

- **Production**: Resources tagged `Environment=production` or `prod` are **never** stopped automatically.  
- **Opt-out**: Tag `cost-saver=false` to exclude any resource.  
- Use **`--force`** only when you intentionally bypass these checks (e.g. in a non-prod-only account).  
- Always run **`--dry-run`** first to preview actions.

---

## EventBridge Integration

EventBridge rules trigger the Lambda at fixed times, e.g.:

- **Start**: `cron(0 7 * * ? *)` (07:00 UTC)  
- **Stop**: `cron(0 19 * * ? *)` (19:00 UTC)

See `scheduler/eventbridge.json` for a reference. Full stack (Lambda + IAM + EventBridge) is in `terraform/`.

---

## Lambda Deployment

1. **Package** (include dependencies):

   ```bash
   pip install -r requirements.txt -t package/
   cp -r cli core config scripts lambda_handler.py package/
   cd package && zip -r ../terraform/cost_saver_lambda.zip .
   ```

2. **Deploy** with Terraform:

   ```bash
   cd terraform
   terraform init
   terraform apply
   ```

Set Lambda env var **`COST_SAVER_ENVIRONMENTS`** to a comma-separated list (e.g. `dev,staging,training`) or rely on `config/environments.yaml` in the package.  
Optional: store config in S3 and set **`CONFIG_S3_BUCKET`** and **`CONFIG_S3_KEY`** (see [docs/setup.md](docs/setup.md)).

---

## Monitoring and Cost Estimation

- **Logging**: Structured JSON logs (resource, action, status, timestamp). In Lambda, logs go to CloudWatch Logs.  
- **Estimate**: `cost-saver estimate dev --hours 12` prints approximate savings using built-in hourly rates.  
- For production dashboards, integrate with **AWS Cost Explorer** or **CloudWatch** (e.g. custom metrics: resources stopped, estimated cost saved).

---

## Documentation

- **[docs/setup.md](docs/setup.md)** – Installation, configuration, EventBridge/Lambda, S3 config, security.  
- **[docs/architecture.md](docs/architecture.md)** – Components, data flow, safety, monitoring.

---

## Supported Services

| Service | Actions |
|--------|--------|
| **Amazon RDS** | Start, Stop |
| **Amazon ECS** | Resize (desired count) |
| **Amazon EC2** | Start, Stop |
| **Auto Scaling Groups** | Scale (min, max, desired) |

Optional future support: ElastiCache, OpenSearch, EKS node groups.

---

## Goal

This project provides a **reliable, safe infrastructure cost automation system** for AWS dev/staging/training environments, suitable for unattended operation and significant cost reduction.
