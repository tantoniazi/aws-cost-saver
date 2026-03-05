# ☁️ AWS Cost Saver

Ferramentas para **reduzir custos de infraestrutura na AWS automaticamente**.

Este projeto contém scripts para **ligar, desligar e redimensionar recursos AWS de forma automática**, reduzindo custos em ambientes de desenvolvimento e treinamento.

---

## 🎯 Objetivo

Reduzir custos AWS através de:

* desligamento automático de RDS
* start automático em horário comercial
* resize automático de ECS
* automação via EventBridge

---

## 📦 Serviços suportados

* Amazon RDS
* Amazon ECS
* Amazon EC2

---

## 📁 Estrutura

```
aws-cost-saver
│
├ scripts
│ ├ start-rds.sh
│ ├ stop-rds.sh
│ ├ resize-ecs.sh
│
├ schedules
│ ├ eventbridge.json
│
└ docs
```

---

## ⚙️ Pré-requisitos

* AWS CLI
* credenciais configuradas

```bash
aws configure
```

---

## 🚀 Uso

### Parar RDS

```bash
./scripts/stop-rds.sh my-database
```

---

### Iniciar RDS

```bash
./scripts/start-rds.sh my-database
```

---

### Resize ECS

```bash
./scripts/resize-ecs.sh cluster-name 1
```

---

## ⏰ Automação

Pode ser integrado com **AWS EventBridge**.

Exemplo:

```
19:00 → stop RDS
07:00 → start RDS
```

---

## 💰 Economia estimada

Ambientes dev/test podem economizar até:

```
60% – 80%
```

do custo mensal.

---

## 🤝 Contribuição

Sugestões:

* suporte a Lambda
* automação Terraform
* integração com CloudWatch

---

## 📄 Licença

MIT
