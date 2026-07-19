# fastAPIWebApp

[![license](https://img.shields.io/github/license/mashape/apistatus.svg?maxAge=2592000)](https://github.com/skondla/flaskAPIWebApp/blob/main/LICENSE)
[![slack](https://img.shields.io/badge/slack-chat-yellow)](https://join.slack.com/t/devops-zwf1016/shared_invite/zt-1wsafgivm-iI88~ZqZBaKGzYhD8N2JsA)
[![CICD](https://github.com/skondla/flaskAPIWebApp/actions/workflows/Deploy-GKE-flaskAdminApp.yml/badge.svg?event=push)](https://github.com/skondla/flaskAPIWebApp/actions)
[![CICD](https://github.com/skondla/flaskAPIWebApp/actions/workflows/Deploy-GKE-flaskUserApp.yml/badge.svg?event=push)](https://github.com/skondla/flaskAPIWebApp/actions)
[![CICD](https://github.com/skondla/flaskAPIWebApp/actions/workflows/Deploy-EKS-ADMIN.yml/badge.svg?event=push)](https://github.com/skondla/flaskAPIWebApp/actions)
[![CICD](https://github.com/skondla/flaskAPIWebApp/actions/workflows/Deploy-EKS-USER.yml/badge.svg?event=push)](https://github.com/skondla/flaskAPIWebApp/actions)
[![Twitter Follow](https://img.shields.io/twitter/follow/skondla?style=social)](https://twitter.com/skondla)

A multi-cloud, containerized web application and REST API for managing AWS RDS database operations — including restore from snapshot, status monitoring, and cluster attachment. Deployed on Kubernetes (EKS, GKE) with a full DevSecOps pipeline via GitHub Actions and ArgoCD GitOps.

> **Flask → FastAPI Migration** — Both the USER and ADMIN applications have been fully converted from Flask to FastAPI (Python 3.11, Uvicorn, JWT OAuth 2.0, Pydantic v2, OWASP Top 10 middleware). The FastAPI versions live in `dockerized/USER_FASTAPI/` and `dockerized/ADMIN_FASTAPI/`. The original Flask source files in `dockerized/USER/` and `dockerized/ADMIN/` are retained as legacy reference.

> **Agentic AI Orchestration** — USER_FASTAPI includes a [LangGraph](https://langchain-ai.github.io/langgraph/)-powered ReAct agent (`lib/agent_orchestrator.py`) that plans and executes the restore → status-check → optional-attach → notify workflow as a single operation, via `GET/POST /agent/restore-workflow`. See [Agentic Restore Workflow](#agentic-restore-workflow--langgraph-orchestration) below.

> **Gap Closure & AI-Native DevSecOps** — Every gap category from the external expert analysis (enforcement, supply chain, secrets & identity, runtime policy, delivery discipline, observability & SRE, governance, modernization) has been addressed. Highlights: RS256 JWT with refresh rotation + server-side revocation, SLSA provenance + Kyverno admission verification of signed/attested images, DAST on pull requests, committed SLOs/alerts/dashboards with OpenTelemetry, full governance paperwork (SECURITY.md, ADRs, CODEOWNERS, IR/DR/retention policies), and an AI layer — SARIF triage agent, AI code review, AI runbook generator, and an MCP server ([`ai/`](ai/), [`.mcp.json`](.mcp.json)). The finding-by-finding map is in [docs/gap-closure.md](docs/gap-closure.md).

---

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
  - [High-Level System Architecture](#high-level-system-architecture)
  - [Application Component Architecture](#application-component-architecture)
  - [Deployment Topology — Multi-Cloud Kubernetes](#deployment-topology--multi-cloud-kubernetes)
- [Technology Stack](#technology-stack)
- [Application Structure](#application-structure)
- [API Endpoints](#api-endpoints)
- [Database Schema](#database-schema)
- [Data Flow Diagrams](#data-flow-diagrams)
  - [Authentication & JWT Issuance](#authentication--jwt-issuance)
  - [RDS Restore Operation — End-to-End](#rds-restore-operation--end-to-end)
  - [Agentic Restore Workflow — LangGraph Orchestration](#agentic-restore-workflow--langgraph-orchestration)
  - [Request Pipeline & OWASP Middleware Chain](#request-pipeline--owasp-middleware-chain)
- [Network Architecture](#network-architecture)
  - [AWS VPC & EKS Network Topology](#aws-vpc--eks-network-topology)
  - [Kubernetes Service Mesh & Pod Networking](#kubernetes-service-mesh--pod-networking)
  - [Ingress & TLS Termination Flow](#ingress--tls-termination-flow)
- [Infrastructure](#infrastructure)
  - [Cluster Admission Policies — Kyverno](#cluster-admission-policies--kyverno)
- [CI/CD Pipeline](#cicd-pipeline)
  - [DevSecOps Pipeline — 10-Stage Flow](#devsecops-pipeline--10-stage-flow)
  - [Pipeline Stage Dependency Graph](#pipeline-stage-dependency-graph)
  - [GitOps Reconciliation Loop (ArgoCD)](#gitops-reconciliation-loop-argocd)
  - [Security Scanning Coverage Matrix](#security-scanning-coverage-matrix)
- [Security Hardening — JWT, Sessions & Rate Limiting](#security-hardening--jwt-sessions--rate-limiting)
- [Observability & SRE](#observability--sre)
- [Governance & Compliance](#governance--compliance)
- [AI-Native DevSecOps](#ai-native-devsecops)
- [Getting Started](#getting-started)
- [Usage — cURL Examples](#usage--curl-examples)
- [Screenshots](#screenshots)
- [Contact](#contact)

---

## Overview

The application exposes both a web interface (HTML/Jinja2) and a REST API for the following AWS RDS operations:

1. **Restore** — Restore an AWS RDS instance or Aurora cluster from a snapshot.
2. **Status** — Check the restore progress of a database instance or cluster.
3. **Attach DB** — Attach a new instance to an existing Aurora DB cluster.
4. **Agent Workflow** — A LangGraph ReAct agent (Claude) plans and executes restore → status → attach → notify as one orchestrated operation instead of three manual steps.
5. **Authentication** — JWT-based login/signup with bcrypt password hashing.
6. **Audit Logging** — Every user action is recorded (email, IP, timestamp, endpoint, request type), including each tool call the agent makes.

Authentication is required for all database operations. User signup is restricted to Admin console users only.

---

## Architecture

### High-Level System Architecture

A bird's-eye view of the full system — clients, the two FastAPI services, persistence, AWS managed services, the CI/CD plane, and the GitOps controller.

```mermaid
flowchart TB
    classDef client fill:#E3F2FD,stroke:#1565C0,stroke-width:2px,color:#0D47A1
    classDef app fill:#E8F5E9,stroke:#2E7D32,stroke-width:2px,color:#1B5E20
    classDef data fill:#FFF3E0,stroke:#E65100,stroke-width:2px,color:#BF360C
    classDef aws fill:#FFEBEE,stroke:#C62828,stroke-width:2px,color:#B71C1C
    classDef cicd fill:#F3E5F5,stroke:#6A1B9A,stroke-width:2px,color:#4A148C
    classDef k8s fill:#E0F7FA,stroke:#00838F,stroke-width:2px,color:#006064
    classDef ai fill:#EDE7F6,stroke:#4527A0,stroke-width:2px,color:#311B92

    subgraph Clients["Clients"]
        B["Browser<br/>HTML + Jinja2"]
        C["cURL or API Client<br/>JSON + Bearer Token"]
        S["Swagger UI<br/>/api/docs"]
    end

    subgraph Edge["Edge — TLS Termination"]
        LB["AWS NLB or ALB<br/>Azure LB or GCP LB<br/>HTTPS"]
    end

    subgraph K8s["Kubernetes EKS GKE AKS"]
        subgraph UserNS["fastapi-namespace"]
            U1["USER_FASTAPI Pod<br/>port 50443<br/>x3 replicas"]
        end
        subgraph AdminNS["fastapi-admin-namespace"]
            A1["ADMIN_FASTAPI Pod<br/>port 30443<br/>x3 replicas"]
        end
        HPA["HPA<br/>min=2 max=10<br/>cpu 70 mem 80"]
    end

    subgraph DataLayer["Data Layer"]
        PG[("PostgreSQL<br/>users · user_info<br/>SQLAlchemy 2.0")]
    end

    subgraph AWSManaged["AWS Managed Services"]
        RDS[("RDS or Aurora<br/>Restore · Status · Attach<br/>via boto3")]
        SES["SES<br/>Email Alerts"]
        ECR[("ECR<br/>Container Registry")]
        SM["Secrets Manager<br/>DB credentials"]
    end

    subgraph Notify["Notifications"]
        SLACK["Slack Webhook"]
    end

    subgraph AgentAI["Agentic Orchestration"]
        CLAUDE["Anthropic Claude API<br/>LangGraph ReAct agent<br/>tool-calling"]
    end

    subgraph Control["Control Plane"]
        GH["GitHub<br/>source of truth"]
        GHA["GitHub Actions<br/>DevSecOps Pipeline"]
        ARGO["ArgoCD<br/>GitOps reconciler"]
    end

    B -->|"HTTPS 50443 or 30443"| LB
    C -->|"HTTPS Bearer"| LB
    S -->|"HTTPS"| LB
    LB --> U1
    LB --> A1
    HPA -.->|scales| U1
    HPA -.->|scales| A1

    U1 -->|"SQL TCP 5432"| PG
    A1 -->|"SQL TCP 5432"| PG
    U1 -->|"HTTPS API"| RDS
    U1 -->|"SMTP"| SES
    U1 -->|"Webhook"| SLACK
    U1 -->|"HTTPS API<br/>tool-calling"| CLAUDE
    U1 -.->|"fetch creds"| SM
    A1 -.->|"fetch creds"| SM

    GH -->|"push"| GHA
    GHA -->|"push image"| ECR
    GHA -->|"kubectl apply"| K8s
    ECR -->|"pull image"| K8s
    ARGO -->|"reconcile"| K8s
    GH -->|"manifests"| ARGO

    class B,C,S client
    class U1,A1 app
    class PG data
    class RDS,SES,ECR,SM aws
    class GH,GHA,ARGO cicd
    class HPA,LB k8s
    class SLACK cicd
    class CLAUDE ai
```

### Application Component Architecture

Internal layering of each FastAPI service — middleware chain, routers, dependencies, and persistence.

```mermaid
flowchart LR
    classDef mw fill:#FFF8E1,stroke:#F57F17,stroke-width:2px,color:#E65100
    classDef route fill:#E8EAF6,stroke:#283593,stroke-width:2px,color:#1A237E
    classDef sec fill:#FCE4EC,stroke:#AD1457,stroke-width:2px,color:#880E4F
    classDef model fill:#E0F2F1,stroke:#00695C,stroke-width:2px,color:#004D40

    REQ([HTTP Request]) --> MW1
    subgraph MWChain["Middleware Chain — LIFO order"]
        direction LR
        MW1["CORS<br/>Middleware"]
        MW2["RateLimit<br/>200/min · 10/min auth"]
        MW3["SecurityHeaders<br/>HSTS · CSP · X-Frame"]
        MW4["SecurityAudit<br/>structured log"]
        MW1 --> MW2 --> MW3 --> MW4
    end

    MW4 --> ROUTER

    subgraph ROUTER["FastAPI Router Dispatch"]
        direction TB
        AUTH["auth.py<br/>/login · /signup · /logout<br/>/auth/token · /auth/refresh<br/>/auth/me · /auth/register"]
        MAIN["main_router.py<br/>/ · /restore · /status<br/>/attachdb · /profile<br/>/agent/restore-workflow"]
    end

    AUTH --> SEC
    MAIN --> SEC

    MAIN -->|"RestoreOrchestrator.run"| AGENT["agent_orchestrator.py<br/>LangGraph create_react_agent<br/>tools: restore · status · attach · notify"]

    subgraph SEC["Security Layer · security.py"]
        direction TB
        JWT["JWT OAuth 2.0<br/>HS256 · 30 min access<br/>7 day refresh"]
        BCRYPT["bcrypt + passlib<br/>+ werkzeug fallback"]
        DEPS["FastAPI Depends<br/>get_current_user<br/>get_optional_user"]
        SSRF["SSRF Guard<br/>validate_rds_endpoint"]
    end

    SEC --> DAL

    subgraph DAL["Data Access Layer"]
        direction TB
        SQLA["SQLAlchemy 2.0<br/>Session per request"]
        MODELS["models.py<br/>User · Userinfo"]
        SCHEMAS["schemas.py<br/>Pydantic v2 DTOs"]
        SQLA --> MODELS
        SQLA --> SCHEMAS
    end

    DAL --> PG[("PostgreSQL")]

    MAIN -->|"boto3"| AWS_RDS[("AWS RDS or Aurora")]
    MAIN -->|"requests"| SLACK([Slack])
    MAIN -->|"mailx"| SES([AWS SES])
    AGENT -->|"rds_ops.py<br/>boto3 · requests · mailx"| AWS_RDS
    AGENT -->|"HTTPS API"| CLAUDE([Anthropic Claude API])

    class MW1,MW2,MW3,MW4 mw
    class AUTH,MAIN route
    class JWT,BCRYPT,DEPS,SSRF sec
    class SQLA,MODELS,SCHEMAS model
    class AGENT,CLAUDE sec
```

### Deployment Topology — Multi-Cloud Kubernetes

The same container image deploys to AWS EKS, GCP GKE, and Azure AKS via cloud-specific Terraform + manifests.

```mermaid
flowchart TB
    classDef aws fill:#FFEBEE,stroke:#C62828,color:#B71C1C
    classDef gcp fill:#E3F2FD,stroke:#1565C0,color:#0D47A1
    classDef az  fill:#E8EAF6,stroke:#283593,color:#1A237E
    classDef gh  fill:#F3E5F5,stroke:#6A1B9A,color:#4A148C

    GH[("GitHub Repo<br/>fastAPIWebApp")]:::gh

    GH --> AWSP
    GH --> GCPP
    GH --> AZP

    subgraph AWSP["AWS — us-east-1"]
        ECR[("ECR<br/>fastapi-user-app<br/>fastapi-admin-app")]:::aws
        EKS["EKS Cluster<br/>fastapi-demo-cluster<br/>private + public subnets<br/>2 AZ · NAT GW"]:::aws
        AWSRDS[("RDS or Aurora<br/>Multi-AZ")]:::aws
        ECR --> EKS
        EKS --> AWSRDS
    end

    subgraph GCPP["GCP — us-central1"]
        GCR[("Artifact Registry")]:::gcp
        GKE["GKE Cluster<br/>VPC-native · regional<br/>workload identity"]:::gcp
        CSQL[("Cloud SQL Postgres")]:::gcp
        GCR --> GKE
        GKE --> CSQL
    end

    subgraph AZP["Azure — eastus"]
        ACR[("Azure ACR<br/>fastapiregistry")]:::az
        AKS["AKS Cluster<br/>fastapi-aks-cluster<br/>VNet + system pool"]:::az
        AZDB[("Azure Database<br/>for PostgreSQL")]:::az
        ACR --> AKS
        AKS --> AZDB
    end
```

---

## Technology Stack

### FastAPI Applications (current)

| Layer | ADMIN_FASTAPI | USER_FASTAPI |
|---|---|---|
| Language | Python 3.11 | Python 3.11 |
| Web Framework | **FastAPI** | **FastAPI** |
| ASGI Server | **Uvicorn** | **Uvicorn** |
| Templating | Jinja2 | Jinja2 |
| Authentication | **JWT OAuth 2.0 — RS256** keypair (HS256 dev fallback), `jti` claims | **JWT OAuth 2.0 — RS256** keypair (HS256 dev fallback), `jti` claims |
| Session Security | Refresh rotation-on-use + reuse detection, server-side `jti` denylist | Refresh rotation-on-use + reuse detection, server-side `jti` denylist |
| Token/Limit State | **Redis** (`token_store.py`; in-process fallback) | **Redis** (`token_store.py`; in-process fallback) |
| Password Hashing | bcrypt (passlib) + werkzeug fallback | bcrypt (passlib) + werkzeug fallback |
| Schema Validation | **Pydantic v2** | **Pydantic v2** |
| ORM | SQLAlchemy 2.0 | SQLAlchemy 2.0 |
| Database | PostgreSQL (psycopg2) | PostgreSQL (psycopg2) |
| Security | OWASP Top 10 middleware, **globally-enforced rate limits**, security headers, CORS allowlist | OWASP Top 10 middleware, **globally-enforced rate limits**, security headers, CORS allowlist, SSRF guard |
| Observability | Prometheus `/metrics`, OpenTelemetry (OTLP), JSON logs, `/healthz` | Prometheus `/metrics`, OpenTelemetry (OTLP), JSON logs, `/healthz` |
| AWS SDK | boto3 / botocore | boto3 / botocore |
| HTTP Client | requests | requests |
| Agentic Orchestration | — | **LangGraph** ReAct agent + **LangChain** tools over **Claude** (Anthropic) |
| Testing | pytest + httpx | pytest + httpx |
| Port | 30443 (HTTPS) | 50443 (HTTPS) |

### Flask Applications (legacy reference)

| Layer | ADMIN (Flask) | USER (Flask) |
|---|---|---|
| Language | Python 3.9 | Python 3.9 |
| Web Framework | Flask | Flask |
| WSGI Server | mod_wsgi (httpd) | mod_wsgi |
| Authentication | Flask-Login | Flask-Login |
| Password Hashing | werkzeug pbkdf2:sha256 | werkzeug pbkdf2:sha256 |
| ORM | Flask-SQLAlchemy | Flask-SQLAlchemy |

### Infrastructure

| Infrastructure | Technology |
|---|---|
| Containerization | Docker (Python 3.11-slim) |
| Orchestration | Kubernetes (EKS, GKE, AKS) |
| Manifest templating | Kustomize (per app × cloud base, `images:` transform for the deploy-time tag) |
| IaC | Terraform (modular, AWS) |
| CI/CD | GitHub Actions — 10-stage pipeline, all scan gates blocking, concurrency guards, DAST on PRs, reusable scan workflow |
| GitOps | **ArgoCD** — sole applier of cluster state (CI calls the ArgoCD API only) |
| Supply-chain integrity | cosign (keyless signing) + syft SBOM (SPDX) + **SLSA provenance** attestations, verified at admission |
| Admission policy | **Kyverno** — signed/attested images only, PSS `restricted`, generated default-deny NetworkPolicy, `:latest` ban ([`kubernetes/policies/`](kubernetes/policies/)) |
| Secrets | Secrets Store CSI Driver → AWS Secrets Manager / Azure Key Vault / GCP Secret Manager |
| Network security | Kubernetes NetworkPolicy (ingress/egress baseline, all 6 app × cloud combos) + Kyverno-generated default-deny |
| Security Scanning | Trivy (CRITICAL/HIGH, blocking), Checkov (blocking) |
| Observability | Prometheus + Grafana operators **plus committed practice**: PrometheusRule SLO alerts, Grafana dashboard, ServiceMonitor, SLOs ([`docs/slo.md`](docs/slo.md)), synthetic monitor |
| AI tooling | **Claude (Anthropic)** — SARIF triage agent, AI code review, runbook generator, MCP server ([`ai/`](ai/)); Renovate; pre-commit hooks |
| Message Queue | RabbitMQ (K8s operator) |
| Cloud Providers | AWS (primary), GCP, Azure |
| TLS | Self-signed certs (containers) / ACM (AWS ALB) |

---

## Application Structure

```
fastAPIWebApp/
├── dockerized/
│   ├── ADMIN_FASTAPI/            # ✅ FastAPI Admin Portal (converted from ADMIN/)
│   │   ├── main.py               # FastAPI app: middleware, router includes, exception handler
│   │   ├── database.py           # SQLAlchemy 2.0 engine + session factory
│   │   ├── models.py             # ORM: User, Users (SQLAlchemy DeclarativeBase)
│   │   ├── schemas.py            # Pydantic v2: UserCreate, UserResponse, Token
│   │   ├── security.py           # JWT OAuth 2.0: RS256 signing, refresh rotation, revocation
│   │   ├── security_middleware.py# OWASP Top 10: security headers, global rate-limit, audit log
│   │   ├── token_store.py        # Redis/in-process store: jti denylist, refresh families, rate counters
│   │   ├── telemetry.py          # Prometheus /metrics, OTel tracing, JSON logs (env-gated)
│   │   ├── routers/
│   │   │   ├── auth.py           # /login /signup /logout + /auth/token /auth/me /auth/register
│   │   │   └── main_router.py    # / (index), /profile (protected)
│   │   ├── templates/            # Jinja2 HTML: base, index, login, signup, profile
│   │   ├── Dockerfile            # Python 3.11-slim, Uvicorn, self-signed TLS, port 30443
│   │   ├── startup.sh            # Container entrypoint: sets env vars, starts Uvicorn
│   │   └── requirements.txt      # fastapi, uvicorn, sqlalchemy, passlib, python-jose, ...
│   │
│   ├── USER_FASTAPI/             # ✅ FastAPI User App (converted from USER/)
│   │   ├── main.py               # FastAPI app: middleware, exception handler
│   │   ├── database.py           # SQLAlchemy 2.0 engine + session factory
│   │   ├── models.py             # ORM: User, Userinfo
│   │   ├── schemas.py            # Pydantic v2: UserCreate, Token, RestoreRequest, ...
│   │   ├── security.py           # JWT OAuth 2.0 (RS256 + rotation + revocation) + werkzeug migration
│   │   ├── security_middleware.py# OWASP Top 10 middleware + SSRF endpoint validation
│   │   ├── token_store.py        # Redis/in-process store: jti denylist, refresh families, rate counters
│   │   ├── telemetry.py          # Prometheus /metrics, OTel tracing, JSON logs (env-gated)
│   │   ├── routers/
│   │   │   ├── auth.py           # /login /signup /logout + OAuth2 API endpoints
│   │   │   └── main_router.py    # / /restore /status /attachdb /agent/restore-workflow
│   │   ├── lib/
│   │   │   ├── rdsAdmin.py       # RDS: RDSDescribe, RDSCreate, RDSRestore, RDSDelete
│   │   │   ├── rds_ops.py        # Shared restore/status/attach/notify wrappers
│   │   │   ├── agent_orchestrator.py # LangGraph ReAct agent — plans/executes the restore workflow
│   │   │   └── utils.py          # AWS Secrets Manager helper
│   │   ├── templates/            # Jinja2 HTML: base, login, signup, restore, status, attachdb, agent_workflow
│   │   ├── docs/                 # API docs (api.md, architecture.drawio)
│   │   ├── Dockerfile            # Python 3.11-slim, Uvicorn, self-signed TLS, port 50443
│   │   ├── startup.sh            # Container entrypoint
│   │   └── requirements.txt      # fastapi, uvicorn, sqlalchemy, passlib, boto3, ...
│   │
│   ├── ADMIN/                    # ⚠️  Flask Admin (legacy — see ADMIN_FASTAPI/ for FastAPI)
│   │   ├── main.py               # Flask Blueprint: / /profile
│   │   ├── auth.py               # Flask Blueprint: /login /signup /logout
│   │   ├── models.py             # Flask-SQLAlchemy: User, Users
│   │   ├── lib/
│   │   │   ├── rdsAdmin.py       # RDS operations
│   │   │   └── sesAdmin.py       # SES email
│   │   ├── templates/            # Jinja2 HTML (Flask url_for — not compatible with FastAPI)
│   │   ├── Dockerfile            # Python 3.9.13, mod_wsgi, port 30443
│   │   └── requirements.txt      # flask, flask-login, flask-sqlalchemy, ...
│   │
│   ├── USER/                     # ⚠️  Flask User App (legacy — see USER_FASTAPI/ for FastAPI)
│   │   ├── main.py               # Flask Blueprint: / /restore /status /attachdb
│   │   ├── auth.py               # Flask Blueprint: auth + RDS operations
│   │   ├── models.py             # Flask-SQLAlchemy: User, Userinfo
│   │   ├── lib/
│   │   │   ├── rdsAdmin.py       # RDS classes
│   │   │   └── sesAdmin.py       # SES email
│   │   ├── templates/            # Jinja2 HTML (Flask url_for)
│   │   ├── Dockerfile            # Python 3.9.13, port 50443
│   │   └── requirements.txt      # flask, flask-login, flask-sqlalchemy, ...
│   │
│   └── DB/
│       └── schema/
│           └── flaskapp.sql      # PostgreSQL schema: users + user_info tables
│
├── provisioning/
│   └── terraform/aws/web_infra/  # Modular Terraform for AWS
│       ├── main.tf               # Root module, provider config
│       ├── variables.tf          # Input variables
│       ├── outputs.tf            # Output values
│       └── modules/
│           ├── vpc/              # VPC + public/private subnets (us-west-2)
│           ├── nat_gateway/      # NAT gateway for private subnet egress
│           ├── security_groups/  # Inbound/outbound rules
│           ├── alb/              # Application Load Balancer
│           ├── ec2/app/          # App server EC2 instances
│           ├── ec2/bastion/      # Bastion host for SSH access
│           ├── route_tables/     # Route table associations
│           ├── subnets/          # Subnet definitions
│           ├── acm/              # AWS Certificate Manager (TLS)
│           └── vpc-endpoint-s3/  # S3 VPC endpoint (private subnet)
│
├── aws/
│   ├── ecr/                      # ECR repo setup/destroy scripts
│   ├── ecs/                      # ECS task definitions + IAM policies
│   ├── eks/                      # EKS cluster scripts + K8s manifests
│   └── web_infra/                # Additional AWS web infra scripts
│
├── gcp/
│   └── gke/deploy/manifests/flaskapp1/
│       ├── Deployment_admin_ui.yaml   # 3-replica admin deployment
│       ├── Deployment_user_ui.yaml    # User app deployment
│       ├── Service_admin_ui.yaml      # K8s service for admin
│       └── Service_user_ui.yaml       # K8s service for user
│
├── kubernetes/
│   ├── operators/                # Grafana, Prometheus, RabbitMQ operators
│   ├── policies/                 # Kyverno admission: verify signed/attested images, PSS
│   │                             #   restricted, default-deny netpol generation, :latest ban
│   └── observability/            # Committed practice: PrometheusRule SLO alerts,
│                                 #   AlertmanagerConfig, Grafana dashboard, ServiceMonitor
│
├── argocd/                       # Real ArgoCD (sole applier) — install script + Application CRs
│   ├── helm/argocd.sh            # Installs argo/argo-cd (previously mislabeled: installed Argo Workflows)
│   └── apps/                     # 6 Application CRs — one per app x cloud, syncPolicy.automated
│
├── actions/                      # Workflow sources (deployed to .github/workflows/)
│   ├── devsecops-fastapi-*.yml   # EKS / GKE / AKS pipelines — gates blocking, concurrency
│   │                             #   guard, cosign sign + SBOM + SLSA provenance, DAST on PRs
│   ├── reusable-security-scans.yml # workflow_call: shared secret/SAST/SCA/IaC stages
│   ├── ai-code-review.yml        # Claude reviews every PR (advisory; CODEOWNERS still gate)
│   ├── ai-security-triage.yml    # Nightly Claude triage of open code-scanning alerts
│   ├── synthetic-monitor.yml     # External /healthz probe every 10 min → Slack
│   └── trivy-scan.yaml           # Trivy CRITICAL vulnerability scanning → SARIF
│
├── ai/                           # AI-native DevSecOps layer (ADR-0005)
│   ├── triage/sarif_triage.py    # Dedupe + rank open alerts, propose fixes → rolling issue
│   ├── runbooks/generate_runbook.py # Draft postmortems & alert runbooks
│   └── mcp/devsecops_mcp_server.py  # MCP server: posture, alerts, pipelines, deployments
│
├── docs/
│   ├── slo.md                    # SLIs/SLOs, error-budget policy, alerting policy
│   ├── gap-closure.md            # Finding-by-finding map of the expert-analysis gaps
│   ├── adr/                      # Architecture decision records (0001–0005)
│   └── governance/               # Incident response, DR (RTO/RPO), data classification,
│                                 #   audit-log retention, branching strategy
│
├── .github/                      # CODEOWNERS, PR template, issue templates
├── .mcp.json                     # Registers the DevSecOps MCP server for Claude Code
├── .pre-commit-config.yaml       # GitLeaks + Bandit + hygiene hooks at the keyboard
├── renovate.json                 # Automated dependency PRs, pinned action digests
├── SECURITY.md · CONTRIBUTING.md · CHANGELOG.md
│
└── images/                       # Documentation screenshots
```

---

## API Endpoints

### USER_FASTAPI (port `50443`)

#### Web UI (HTML, cookie-based JWT)

| Method | Endpoint | Auth Required | Description |
|---|---|---|---|
| `GET` | `/` | No | Landing page |
| `GET` | `/login` | No | Login form |
| `POST` | `/login` | No | Authenticate; sets JWT HttpOnly cookie |
| `GET` | `/signup` | No | Signup form |
| `POST` | `/signup` | No | Create account (bcrypt-hashed password) |
| `GET` | `/logout` | No | Revoke tokens server-side (jti denylist + refresh family), clear cookies |
| `GET` | `/restore` | Yes | Restore DB form |
| `POST` | `/restore` | Yes | Restore RDS instance or Aurora cluster from snapshot |
| `GET` | `/status` | Yes | Status check form |
| `POST` | `/status` | Yes | Poll RDS restore / instance status |
| `GET` | `/attachdb` | Yes | Attach DB form |
| `POST` | `/attachdb` | Yes | Create and attach instance to Aurora cluster |
| `GET` | `/agent/restore-workflow` | Yes | Agent workflow form (snapshot, source endpoint, optional target instance class + goal) |
| `POST` | `/agent/restore-workflow` | Yes | LangGraph agent plans/executes restore → status → optional attach → notify in one call |

#### OAuth2 / REST API (JSON, Bearer token)

| Method | Endpoint | Auth Required | Description |
|---|---|---|---|
| `POST` | `/auth/token` | No | OAuth2 password flow — returns access + refresh tokens |
| `POST` | `/auth/refresh` | No (refresh cookie) | **Rotation-on-use:** returns new access + new refresh; replaying a rotated token revokes the whole family (theft detection) |
| `GET` | `/auth/me` | Yes | Return current user profile |
| `POST` | `/auth/register` | No | Register new user (API, returns JSON) |
| `GET` | `/healthz` | No | Liveness / synthetic-monitor probe (no DB dependency) |
| `GET` | `/metrics` | No | Prometheus metrics (scraped via ServiceMonitor) |
| `GET` | `/api/docs` | No | Swagger UI |
| `GET` | `/api/redoc` | No | ReDoc |

### ADMIN_FASTAPI (port `30443`)

#### Web UI (HTML, cookie-based JWT)

| Method | Endpoint | Auth Required | Description |
|---|---|---|---|
| `GET` | `/` | No | Admin portal landing page |
| `GET` | `/login` | No | Admin login form |
| `POST` | `/login` | No | Authenticate; sets JWT HttpOnly cookie |
| `GET` | `/signup` | No | Admin signup form |
| `POST` | `/signup` | No | Create admin account |
| `GET` | `/logout` | No | Clear auth cookies |
| `GET` | `/profile` | Yes | Authenticated admin profile page |

#### OAuth2 / REST API (JSON, Bearer token)

| Method | Endpoint | Auth Required | Description |
|---|---|---|---|
| `POST` | `/auth/token` | No | OAuth2 password flow |
| `POST` | `/auth/refresh` | No (refresh cookie) | Rotation-on-use refresh (reuse detection revokes the family) |
| `GET` | `/auth/me` | Yes | Return current admin profile |
| `POST` | `/auth/register` | No | Register admin user (API, returns JSON) |
| `GET` | `/healthz` | No | Liveness / synthetic-monitor probe |
| `GET` | `/metrics` | No | Prometheus metrics |
| `GET` | `/api/docs` | No | Swagger UI |
| `GET` | `/api/redoc` | No | ReDoc |

---

## Database Schema

PostgreSQL, managed via SQLAlchemy ORM. The `flaskapp.sql` bootstrap file creates:

```sql
-- Registered users
CREATE TABLE users (
    id       SERIAL PRIMARY KEY,
    email    VARCHAR(100) UNIQUE NOT NULL,
    password VARCHAR(1000) NOT NULL,   -- bcrypt hash
    name     VARCHAR(1000) NOT NULL
);

-- Audit / activity log
CREATE TABLE user_info (
    id          SERIAL PRIMARY KEY,
    email       VARCHAR(100) NOT NULL,
    ip          VARCHAR(50)  NOT NULL,  -- real IP via X-Forwarded-For
    time        VARCHAR(60)  NOT NULL,  -- YYYYMMDDHHmm
    requesttype VARCHAR(30),            -- GET / POST
    endpoint    VARCHAR(100),           -- e.g. /restore
    comments    VARCHAR(200)
);
```

---

## Data Flow Diagrams

### Authentication & JWT Issuance

OAuth 2.0 password-flow with bcrypt verification and HttpOnly cookie + Bearer header dual-mode auth. See [`security.py`](dockerized/USER_FASTAPI/security.py) and [`routers/auth.py`](dockerized/USER_FASTAPI/routers/auth.py).

```mermaid
sequenceDiagram
    autonumber
    actor User as "Client<br/>Browser or API"
    participant LB as "NLB<br/>port 50443"
    participant MW as "Middleware Chain<br/>rate-limit · headers · audit"
    participant Auth as "auth.py<br/>POST /auth/token"
    participant Sec as "security.py"
    participant DB as "PostgreSQL<br/>users table"

    User->>LB: POST /auth/token<br/>username + password
    LB->>MW: forward HTTPS
    MW->>MW: rate-limit check<br/>10/min for /auth
    MW->>Auth: dispatch
    Auth->>DB: SELECT * FROM users WHERE email = ?
    DB-->>Auth: user row + hashed pw
    Auth->>Sec: verify_password plain, hashed

    alt bcrypt matches
        Sec-->>Auth: True
    else fallback to werkzeug pbkdf2
        Sec->>Sec: check_password_hash legacy
        Sec-->>Auth: True or False
    end

    alt credentials valid
        Auth->>Sec: create_access_token<br/>sub=email · exp=30m
        Auth->>Sec: create_refresh_token<br/>sub=email · exp=7d
        Sec-->>Auth: access_jwt + refresh_jwt
        Auth-->>User: 200 OK<br/>access_token + refresh_token<br/>Set-Cookie HttpOnly
    else credentials invalid
        Auth-->>User: 401 Unauthorized<br/>WWW-Authenticate Bearer
    end

    Note over User,DB: Subsequent protected request

    User->>LB: GET /restore<br/>Cookie access_token=Bearer JWT
    LB->>MW: forward
    MW->>Sec: get_current_user via Depends
    Sec->>Sec: decode JWT<br/>HS256 · SECRET_KEY
    Sec->>DB: lookup user by sub claim
    DB-->>Sec: user
    Sec-->>MW: User object
    MW-->>User: 200 OK<br/>restore page HTML
```

### RDS Restore Operation — End-to-End

Full data flow for `POST /restore` — from form submission through AWS RDS API call to multi-channel notification and audit logging.

```mermaid
sequenceDiagram
    autonumber
    actor U as "Authenticated User"
    participant API as "USER_FASTAPI<br/>POST /restore"
    participant SSRF as "SSRF Validator<br/>validate_rds_endpoint"
    participant RDS as "boto3 RDS Client"
    participant AWS as "AWS RDS or Aurora"
    participant PG as "PostgreSQL<br/>user_info audit table"
    participant SLACK as "Slack Webhook"
    participant SES as "AWS SES"

    U->>API: POST /restore<br/>snapshotname + endpoint
    API->>API: get_optional_user<br/>enforce auth
    API->>SSRF: validate_rds_endpoint endpoint

    alt invalid hostname<br/>private IP or non-RDS pattern
        SSRF-->>API: raise ValueError
        API-->>U: 400 Bad Request
    else valid AWS RDS hostname
        SSRF-->>API: ok
        API->>RDS: dbInstanceInfo endpoint
        RDS->>AWS: DescribeDBInstances or DescribeDBClusters
        AWS-->>RDS: SG · subnet · engine · version · class
        RDS-->>API: instance metadata

        alt endpoint is cluster
            API->>RDS: restore_db_cluster_from_snapshot
            RDS->>AWS: RestoreDBClusterFromSnapshot
        else endpoint is instance
            API->>RDS: restore_db_instance_from_db_snapshot
            RDS->>AWS: RestoreDBInstanceFromDBSnapshot
        end
        AWS-->>RDS: DBClusterIdentifier or DBInstanceIdentifier
        RDS-->>API: success

        API->>RDS: getDBClusterStatus or getDBInstanceStatus
        RDS->>AWS: DescribeDB
        AWS-->>RDS: state creating · available
        RDS-->>API: db_state

        par audit log
            API->>PG: INSERT INTO user_info<br/>email · ip · time · requesttype · endpoint
            PG-->>API: ok
        and Slack notification
            API->>SLACK: POST channel + text + icon_emoji
            SLACK-->>API: 200
        and email alert
            API->>SES: mailx -s dB Restore distro
            SES-->>API: queued
        end

        API-->>U: 202 Accepted<br/>Database X is being restored<br/>New Endpoint and Status returned
    end
```

### Agentic Restore Workflow — LangGraph Orchestration

`POST /agent/restore-workflow` replaces three manual form submissions (restore, status, attach) with a single call. A LangGraph `create_react_agent` ReAct loop plans and executes the minimum necessary tool calls — capped at 8 tool calls and 30s of total poll-wait so it stays inside one HTTP request. See [`lib/agent_orchestrator.py`](dockerized/USER_FASTAPI/lib/agent_orchestrator.py).

```mermaid
sequenceDiagram
    autonumber
    actor U as "Authenticated User"
    participant API as "USER_FASTAPI<br/>POST /agent/restore-workflow"
    participant ORC as "RestoreOrchestrator<br/>agent_orchestrator.py"
    participant GRAPH as "LangGraph<br/>create_react_agent"
    participant LLM as "Claude<br/>Anthropic API"
    participant TOOLS as "LangChain Tools<br/>rds_ops.py"
    participant AWS as "AWS RDS or Aurora"
    participant PG as "PostgreSQL<br/>user_info audit table"

    U->>API: POST /agent/restore-workflow<br/>snapshotname + endpoint + goal (optional)
    API->>API: get_optional_user · enforce auth
    API->>ORC: run goal, snapshot_name, source_endpoint, target_instance_class
    ORC->>GRAPH: stream messages=[goal] · system=SYSTEM_PROMPT · tools

    loop up to 8 tool calls
        GRAPH->>LLM: invoke messages + tool schemas
        LLM-->>GRAPH: AIMessage — tool_call or final text

        alt tool_call requested
            GRAPH->>TOOLS: dispatch e.g. restore_snapshot · check_db_status · attach_instance · notify
            TOOLS->>AWS: boto3 RDS API call
            AWS-->>TOOLS: state / identifiers
            TOOLS-->>GRAPH: ToolMessage result
            GRAPH->>ORC: on_step callback tool, input, result
            ORC->>PG: INSERT INTO user_info<br/>"Agent: {tool}" · result[:200]
        else final answer
            GRAPH-->>ORC: plain-text summary
        end
    end

    ORC-->>API: OrchestrationResult final_message + steps[]
    API-->>U: 202 Accepted<br/>step-by-step transcript + summary
```

### Request Pipeline & OWASP Middleware Chain

Every request traverses four middleware layers before reaching a route handler. Order is LIFO — last added runs first.

```mermaid
flowchart TB
    classDef pass fill:#E8F5E9,stroke:#2E7D32,color:#1B5E20
    classDef block fill:#FFEBEE,stroke:#C62828,color:#B71C1C
    classDef route fill:#E8EAF6,stroke:#283593,color:#1A237E
    classDef phase fill:#FFF8E1,stroke:#F57F17,color:#E65100

    REQ([HTTPS Request]):::phase

    subgraph REQPATH["Request Path  (outer to inner)"]
        direction TB
        AUDIT_IN["1. SecurityAuditMiddleware<br/>start timer · capture client IP"]:::pass
        RATE{"2. RateLimitMiddleware<br/>200/min general<br/>10/min auth endpoints"}
        R429["429 Too Many Requests<br/>Retry-After 60"]:::block
        HDR_IN["3. SecurityHeadersMiddleware<br/>pass-through on request"]:::pass
        CORS["4. CORSMiddleware<br/>origin · methods · headers"]:::pass
    end

    ROUTE["FastAPI Router Dispatch<br/>Depends get_current_user · get_db"]:::route

    subgraph HANDLERS["Route Handler Outcomes"]
        direction TB
        OK(["200 / 2xx Response"]):::pass
        REDIR["401 on HTML request<br/>302 to /login?next=PATH"]:::block
        JSON401["401 on JSON request<br/>WWW-Authenticate Bearer"]:::block
        ERR(["4xx or 5xx Error"]):::block
    end

    subgraph RESPATH["Response Path  (inner to outer)"]
        direction TB
        HDR_OUT["SecurityHeadersMiddleware<br/>inject HSTS · CSP · X-Frame<br/>nosniff · Referrer-Policy"]:::pass
        AUDIT_OUT["SecurityAuditMiddleware<br/>log method · path · status<br/>ip · ua · duration_ms"]:::pass
    end

    OUT([HTTPS Response]):::phase

    REQ --> AUDIT_IN
    AUDIT_IN --> RATE
    RATE -->|under limit| HDR_IN
    RATE -->|over limit| R429
    HDR_IN --> CORS
    CORS --> ROUTE

    ROUTE --> OK
    ROUTE --> REDIR
    ROUTE --> JSON401
    ROUTE --> ERR

    OK --> HDR_OUT
    REDIR --> HDR_OUT
    JSON401 --> HDR_OUT
    ERR --> HDR_OUT
    R429 --> HDR_OUT

    HDR_OUT --> AUDIT_OUT
    AUDIT_OUT --> OUT
```

---

## Network Architecture

### AWS VPC & EKS Network Topology

Defined in [`aws/eks/deploy/terraform/`](aws/eks/deploy/terraform/) — `192.168.0.0/16` VPC across two AZs with public/private subnet pairs.

```mermaid
flowchart TB
    classDef public fill:#E3F2FD,stroke:#1565C0,color:#0D47A1
    classDef private fill:#FFF3E0,stroke:#E65100,color:#BF360C
    classDef ctrl fill:#F3E5F5,stroke:#6A1B9A,color:#4A148C
    classDef ext fill:#ECEFF1,stroke:#37474F,color:#263238

    INET([🌍 Internet]):::ext
    IGW[Internet Gateway]:::ctrl

    INET <--> IGW

    subgraph VPC["VPC k8svpc · 192.168.0.0/16 · us-east-1"]
        direction TB

        subgraph AZA["Availability Zone us-east-1a"]
            PUBA["public-us-east-1a<br/>192.168.64.0/19<br/>map_public_ip=true<br/>tag kubernetes.io/role/elb"]:::public
            PRIA["private-us-east-1a<br/>192.168.0.0/19<br/>tag kubernetes.io/role/internal-elb"]:::private
            NATA["NAT Gateway A"]:::ctrl
            NLBA["NLB Node A<br/>ports 50443 and 30443"]:::public
            NODEA["EKS Worker<br/>fastapi-user-app pod<br/>fastapi-admin-app pod"]:::private
        end

        subgraph AZB["Availability Zone us-east-1b"]
            PUBB["public-us-east-1b<br/>192.168.96.0/19<br/>map_public_ip=true"]:::public
            PRIB["private-us-east-1b<br/>192.168.32.0/19"]:::private
            NATB["NAT Gateway B"]:::ctrl
            NLBB["NLB Node B"]:::public
            NODEB["EKS Worker<br/>fastapi-user-app pod<br/>fastapi-admin-app pod"]:::private
        end

        EKSCTL["EKS Control Plane<br/>AWS-managed<br/>OIDC provider"]:::ctrl
    end

    RDS[("Amazon RDS or Aurora<br/>Multi-AZ<br/>private subnets")]:::private
    ECR[("Amazon ECR")]:::ext
    SES["Amazon SES"]:::ext
    SLACK["Slack Webhook"]:::ext

    IGW --> PUBA
    IGW --> PUBB
    PUBA --- NLBA
    PUBB --- NLBB
    PUBA --- NATA
    PUBB --- NATB

    NLBA -->|TCP 50443/30443| NODEA
    NLBB -->|TCP 50443/30443| NODEB

    NODEA --- PRIA
    NODEB --- PRIB

    PRIA -->|egress via| NATA
    PRIB -->|egress via| NATB
    NATA --> IGW
    NATB --> IGW

    NODEA -->|TCP 5432| RDS
    NODEB -->|TCP 5432| RDS
    NODEA -->|HTTPS API| ECR
    NODEA -->|SMTP| SES
    NODEA -->|HTTPS| SLACK

    EKSCTL -.manages.- NODEA
    EKSCTL -.manages.- NODEB
```

### Kubernetes Service Mesh & Pod Networking

Per-namespace topology with HPA, NLB, init container DB wait, and pod-level security context. From [`aws/eks/deploy/manifest/fastapi1/`](aws/eks/deploy/manifest/fastapi1/).

```mermaid
flowchart TB
    classDef svc fill:#E0F7FA,stroke:#00838F,color:#006064
    classDef pod fill:#E8F5E9,stroke:#2E7D32,color:#1B5E20
    classDef cfg fill:#FFF8E1,stroke:#F57F17,color:#E65100
    classDef hpa fill:#F3E5F5,stroke:#6A1B9A,color:#4A148C

    EXT([External Client<br/>HTTPS])
    EXT --> NLB

    subgraph NS["Namespace fastapi-namespace"]
        NLB["Service fastapi-user-app<br/>type LoadBalancer NLB<br/>port 50443 to targetPort 50443<br/>backend-protocol tcp"]:::svc

        subgraph DEP["Deployment fastapi-user-app · replicas=3 · RollingUpdate maxSurge=1 maxUnavail=0"]
            direction LR
            P1["Pod 1<br/>uvicorn 50443<br/>nonRoot · seccomp"]:::pod
            P2["Pod 2<br/>uvicorn 50443"]:::pod
            P3["Pod 3<br/>uvicorn 50443"]:::pod
        end

        INIT["initContainer wait-for-db<br/>busybox · nc -z host port<br/>readOnlyRootFs · cap drop ALL"]:::pod

        HPA["HorizontalPodAutoscaler<br/>min=2 max=10<br/>cpu 70 percent · mem 80 percent"]:::hpa

        CSI["SecretProviderClass<br/>syncs AWS Secrets Manager<br/>-> Secret fastapi-db-secret"]:::cfg
        CM["ConfigMap fastapi-config<br/>APP_NAME · APP_PORT<br/>AWS_REGION · LOG_LEVEL"]:::cfg

        SA["ServiceAccount fastapi-sa<br/>IRSA to IAM role RDS SES + Secrets Manager<br/>automountToken=false"]:::cfg

        NETPOL["NetworkPolicy<br/>ingress: app port only<br/>egress: DNS · HTTPS · 5432 only"]:::hpa

        SPREAD["topologySpreadConstraints<br/>maxSkew=1 · hostname<br/>DoNotSchedule"]:::hpa

        TSC["Probes<br/>startup 5s 12fail<br/>readiness 10s<br/>liveness 30s"]:::hpa
    end

    PG[("PostgreSQL<br/>port 5432")]
    RDS[("AWS RDS API<br/>boto3")]

    NLB --> P1
    NLB --> P2
    NLB --> P3

    INIT --> P1
    INIT --> P2
    INIT --> P3

    CSI -.CSI volume + envFrom.-> P1
    CM -.envFrom.-> P1
    SA -.identity.-> P1
    NETPOL -.restricts.-> P1

    HPA -.scales.-> DEP
    SPREAD -.spreads.-> DEP
    TSC -.checks.-> DEP

    P1 -->|5432| PG
    P2 -->|5432| PG
    P3 -->|5432| PG
    P1 -->|IRSA HTTPS| RDS
```

### Ingress & TLS Termination Flow

End-to-end TLS path showing where each hop terminates / re-encrypts.

```mermaid
flowchart LR
    classDef edge fill:#E3F2FD,stroke:#1565C0,color:#0D47A1
    classDef enc fill:#FFEBEE,stroke:#C62828,color:#B71C1C
    classDef plain fill:#FFF8E1,stroke:#F57F17,color:#E65100

    CLIENT([Client]) -->|"HTTPS<br/>public cert or self-signed"| DNS

    DNS["Route 53 or DNS"]:::edge
    DNS --> NLB

    NLB["NLB port 50443<br/>passthrough TCP<br/>no TLS termination"]:::edge
    NLB -->|"TLS still encrypted<br/>NLB acts at L4"| KSVC

    KSVC["K8s Service<br/>type LoadBalancer"]:::edge
    KSVC --> POD

    POD["Pod uvicorn 50443<br/>terminates TLS here<br/>cert mounted at /app/certs"]:::enc
    POD -->|"cleartext localhost"| APP

    APP["FastAPI App<br/>plain HTTP inside pod"]:::plain
    APP -->|"TLS to PG<br/>sslmode=require"| PG[("PostgreSQL")]:::enc
    APP -->|"HTTPS · TLS 1.2+"| RDS[("AWS RDS API")]:::enc
    APP -->|"HTTPS"| SLACK([Slack]):::enc
```

---

## Infrastructure

### AWS — Terraform Modules (`provisioning/terraform/aws/web_infra/`)

| Module | Purpose |
|---|---|
| `vpc` | VPC + public & private subnets across AZs (us-west-2) |
| `nat_gateway` | NAT GW for private subnet internet egress |
| `security_groups` | ALB and app-tier security groups |
| `alb` | Application Load Balancer (HTTPS listener, target groups) |
| `acm` | TLS certificate via AWS Certificate Manager |
| `ec2/app` | Application EC2 instances in private subnet |
| `ec2/bastion` | Bastion host in public subnet for SSH tunneling |
| `route_tables` | Route table associations for public/private subnets |
| `subnets` | Subnet CIDR definitions |
| `vpc-endpoint-s3` | S3 VPC endpoint for private subnet connectivity |

### AWS Container Deployments

- **ECR** — Private container registry for Docker images.
- **ECS** — Fargate task definitions + IAM execution roles.
- **EKS** — Managed Kubernetes; cluster creation/teardown via bash scripts in `aws/eks/`.

### GCP — GKE (`gcp/gke/`)

- Kubernetes manifests for Admin (3 replicas) and User (configurable) deployments.
- `flaskapp1.yaml` — combined manifest.
- LoadBalancer services expose apps externally.

### Kubernetes Operators (`kubernetes/operators/`)

| Operator | Purpose |
|---|---|
| Prometheus | Metrics collection |
| Grafana | Metrics dashboards |
| RabbitMQ | Message queue (for async RDS operations) |

### ArgoCD GitOps (`argocd/`) — sole applier of cluster state

- [`helm/argocd.sh`](argocd/helm/argocd.sh) installs real ArgoCD via the official `argo/argo-cd` chart (this previously installed the unrelated Argo Workflows chart despite the directory name — fixed).
- [`apps/`](argocd/apps/) — one `Application` CR per app × cloud (6 total), each pointing at a Kustomize base under `azure/aks/deploy/manifest/`, `aws/eks/deploy/manifest/`, or `gcp/gke/deploy/manifests/`, with `syncPolicy.automated` (prune + selfHeal).
- CI's `deploy` job no longer runs `kubectl apply` — it calls the ArgoCD API (`argocd app set --kustomize-image` → `sync` → `wait`) and ArgoCD does the actual reconciliation. See [ArgoCD GitOps setup](docs/github-secrets.md#argocd-gitops-setup--sole-applier) for one-time setup and the `CHANGEME` placeholders each Kustomize base needs filled in.

### Secrets Store CSI Driver — replacing the plaintext K8s Secret

Every `fastapi1/` and `fastapi-admin/` manifest directory (all 3 clouds) now ships a `secretproviderclass.yaml` that syncs DB credentials + the JWT signing key from AWS Secrets Manager / Azure Key Vault / GCP Secret Manager into the same `fastapi-db-secret` K8s Secret the app already reads — no application code change. The old plaintext `secret.yaml` is marked deprecated and no longer applied by CI. See [Secrets Store CSI Driver](docs/github-secrets.md#secrets-store-csi-driver-replacing-the-plaintext-k8s-secret) for the cluster-side prerequisites (driver install + IAM bindings) this can't provision from a repo edit alone.

### NetworkPolicy + pod hardening baseline

Every `fastapi1/` and `fastapi-admin/` deployment now ships a `networkpolicy.yaml` (ingress limited to the app port; egress limited to DNS/HTTPS/Postgres — previously zero policies protected these workloads) and the main container runs with `readOnlyRootFilesystem: true` across all three clouds (EKS previously disabled this with a `# uvicorn writes temp files` comment; an `emptyDir` mounted at `/tmp` — also used for the app's log file, see `startup.sh` — makes the read-only root filesystem actually work instead of being switched off).

### Cluster Admission Policies — Kyverno

Manifest-level hardening is now **cluster-enforced** so a future edit (or a manual `kubectl run`) cannot regress it. [`kubernetes/policies/`](kubernetes/policies/) ships four enforced Kyverno ClusterPolicies plus an install script ([ADR-0003](docs/adr/0003-kyverno-admission-control.md)):

| Policy | Enforces |
|---|---|
| [`verify-image-signatures.yaml`](kubernetes/policies/verify-image-signatures.yaml) | Only images with a valid **Cosign keyless signature + SPDX SBOM + SLSA provenance** attestation (from this repo's GitHub Actions OIDC identity) are admitted; tags are rewritten to digests at admission |
| [`require-pod-security.yaml`](kubernetes/policies/require-pod-security.yaml) | PSS `restricted` semantics: non-root, seccomp, all capabilities dropped, no privilege escalation, read-only root FS; PSS labels required on `fastapi-*` namespaces |
| [`require-networkpolicy.yaml`](kubernetes/policies/require-networkpolicy.yaml) | Auto-generates a default-deny NetworkPolicy in every new namespace |
| [`disallow-latest-tag.yaml`](kubernetes/policies/disallow-latest-tag.yaml) | Rejects `:latest` / untagged images |

This closes the supply chain end-to-end: **build → sign/attest (CI) → verify (admission)** — the cluster no longer accepts "anything from the registry". Roll out new policies warn-then-block (Audit → Enforce) per [`kubernetes/policies/README.md`](kubernetes/policies/README.md). Service mesh / mTLS was evaluated and deliberately deferred with recorded revisit triggers ([ADR-0004](docs/adr/0004-defer-service-mesh.md)).

---

## CI/CD Pipeline

Six workflows live under [`.github/workflows/`](.github/workflows/) (sources maintained in [`actions/`](actions/)) — one per (app × cloud) combination plus a standalone Trivy scan, alongside the reusable-scan, AI-review, AI-triage and synthetic-monitor workflows. Each pipeline is a 10-stage DevSecOps flow: secret-scan → SAST → SCA → build → container-scan → IaC-scan → sign/SBOM/provenance → deploy → DAST (post-deploy **and** on PRs) → notify.

> **Every scan gate now blocks the build.** Bandit/Semgrep/pip-audit/Trivy/Checkov/ZAP
> used to run with `|| true` / `exit-code: "0"` / `soft_fail: true` / `fail_action: false`
> — visibility without enforcement. All six now fail the pipeline on High/Critical findings.

Pipeline hardening beyond the gates:

- **Concurrency guard** on every workflow — a new push supersedes an in-flight PR run; deploys to the same ref queue instead of racing (fixes last-write-silently-wins).
- **SLSA provenance** — stage 7 attests how each image was built (workflow, commit, run) with `cosign attest --type slsaprovenance1`, alongside the signature and SPDX SBOM. All three are verified at admission by Kyverno.
- **DAST on pull requests** — a `dast-pr` job builds the candidate image, runs it with a Postgres sidecar on the runner, and gates the PR on an OWASP ZAP baseline scan (FAIL-level alerts block merge). Post-deploy ZAP still runs on `main`/`master`.
- **Reusable scan workflow** — [`reusable-security-scans.yml`](actions/reusable-security-scans.yml) consolidates the previously copy-pasted secret-scan/SAST/SCA/IaC stages behind `workflow_call`, so scanning policy changes are made once, not six times.
- **AI code review** — [`ai-code-review.yml`](actions/ai-code-review.yml) has Claude review every PR with a security-first checklist (advisory; CODEOWNERS approval remains required).

### DevSecOps Pipeline — 10-Stage Flow

```mermaid
flowchart LR
    classDef trigger fill:#FFF8E1,stroke:#F57F17,color:#E65100
    classDef sec fill:#FCE4EC,stroke:#AD1457,color:#880E4F
    classDef build fill:#E0F7FA,stroke:#00838F,color:#006064
    classDef deploy fill:#E8F5E9,stroke:#2E7D32,color:#1B5E20
    classDef dast fill:#F3E5F5,stroke:#6A1B9A,color:#4A148C
    classDef notify fill:#FFEBEE,stroke:#C62828,color:#B71C1C

    PUSH(["git push<br/>main · master · PR"]):::trigger

    PUSH --> S1
    S1["1. Secret Scan<br/>TruffleHog + GitLeaks"]:::sec
    S1 --> S2
    S1 --> S3
    S2["2. SAST<br/>Bandit + Semgrep<br/>p/owasp-top-ten · p/jwt"]:::sec
    S3["3. SCA<br/>pip-audit + Trivy FS<br/>severity HIGH and CRITICAL"]:::sec

    S2 --> S4
    S3 --> S4
    S4["4. Build and Push<br/>docker build to ECR ACR GCR<br/>OIDC auth · no static keys<br/>tag=git.sha + latest"]:::build

    S4 --> S5
    S4 --> S6
    S5["5. Container Scan<br/>Trivy image scan<br/>HIGH and CRITICAL · SARIF"]:::sec
    S6["6. IaC Scan<br/>Checkov Terraform + K8s"]:::sec

    S5 --> S7
    S6 --> S7
    S7["7. Sign · SBOM · Provenance<br/>cosign keyless sign<br/>syft SBOM + SLSA attest"]:::build

    S7 --> S8
    S8["8. Deploy<br/>argocd app set --kustomize-image<br/>argocd app sync and wait<br/>ArgoCD is sole applier"]:::deploy

    S8 --> S9
    S9["9. DAST<br/>OWASP ZAP Baseline<br/>post-deploy on main<br/>+ dast-pr gates PRs"]:::dast

    S8 --> S10
    S9 --> S10
    S10["10. Notify<br/>Slack webhook<br/>deploy + DAST results"]:::notify

    GHSEC[("GitHub Security<br/>Code Scanning tab")]
    S1 -.->|"SARIF"| GHSEC
    S2 -.->|"SARIF"| GHSEC
    S3 -.->|"SARIF"| GHSEC
    S5 -.->|"SARIF"| GHSEC
    S6 -.->|"SARIF"| GHSEC
```

### Pipeline Stage Dependency Graph

Showing job-level `needs:` dependencies (concurrency in green, gates in red).

```mermaid
flowchart TB
    classDef parallel fill:#E8F5E9,stroke:#2E7D32,color:#1B5E20
    classDef gate fill:#FFEBEE,stroke:#C62828,color:#B71C1C
    classDef cond fill:#FFF8E1,stroke:#F57F17,color:#E65100

    subgraph WAVE1["Wave 1 — runs in parallel"]
        direction LR
        J1["secret-scan"]:::parallel
        J2["sast"]:::parallel
        J3["sca"]:::parallel
        J7["iac-scan"]:::parallel
    end

    GATE1{"needs<br/>secret-scan<br/>sast · sca"}:::gate
    WAVE1 --> GATE1
    GATE1 --> J4["build"]:::parallel

    subgraph WAVE2["Wave 2 — parallel after build"]
        direction LR
        J5["container-scan"]:::parallel
        J10["sign-and-sbom"]:::parallel
    end

    J4 --> WAVE2

    GATE2{"needs<br/>build · container-scan<br/>iac-scan · sign-and-sbom"}:::gate
    WAVE2 --> GATE2
    J7 --> GATE2
    GATE2 --> J6["deploy — ArgoCD API only<br/>environment staging or prod<br/>requires approval"]:::parallel

    COND{"ref is main or master?"}:::cond
    J6 --> COND
    J8["dast"]:::parallel
    J9["notify<br/>if always"]:::parallel
    COND -->|"yes"| J8
    COND -->|"no"| J9
    J8 --> J9
    J6 --> J9
```

### GitOps Reconciliation Loop (ArgoCD)

ArgoCD is the **sole applier** of cluster state — CI never runs `kubectl apply`.
The pipeline builds and pushes the image, then calls the ArgoCD API to point
each `Application` (see [`argocd/apps/`](argocd/apps/)) at the new tag and
trigger a sync; ArgoCD (in-cluster, its own service account) does the actual
reconciliation, and keeps polling Git independently of CI. See
[`argocd/helm/argocd.sh`](argocd/helm/argocd.sh) and
[ArgoCD GitOps setup](docs/github-secrets.md#argocd-gitops-setup--sole-applier).

```mermaid
sequenceDiagram
    autonumber
    actor Dev as "Developer"
    participant Repo as "GitHub Repo<br/>source of truth (Kustomize bases)"
    participant GHA as "GitHub Actions"
    participant Reg as "ECR or ACR or GCR"
    participant Argo as "ArgoCD Controller"
    participant K8s as "Kubernetes API"
    participant Pod as "Workload Pods"

    Dev->>Repo: git push<br/>app code (manifests are static Kustomize bases)
    Repo->>GHA: trigger workflow

    Note over GHA: Stages 1 to 7 — sec scans · build · image scan · sign+SBOM
    GHA->>Reg: docker push + cosign sign<br/>tag=git.sha

    GHA->>Argo: argocd app set --kustomize-image tag=git.sha
    GHA->>Argo: argocd app sync --prune
    Argo->>K8s: apply Kustomize-rendered manifests
    K8s->>Pod: rolling update
    Pod-->>K8s: ready
    Argo-->>GHA: argocd app wait --health

    GHA->>GHA: smoke test · ZAP (dast job,<br/>read-only cluster creds)

    loop continuous, independent of CI
        Argo->>Repo: git fetch HEAD
        Argo->>Argo: diff against live state
        alt drift detected
            Argo->>K8s: prune or sync (selfHeal)
            K8s->>Pod: reconcile
        else in sync
            Argo->>Argo: no-op
        end
    end

    Pod-->>K8s: liveness and readiness OK
    K8s-->>Dev: deployment healthy<br/>visible in ArgoCD UI + Slack notify
```

### Security Scanning Coverage Matrix

Each tool maps to specific OWASP Top 10 categories and pipeline stages.

```mermaid
flowchart LR
    classDef tool fill:#FCE4EC,stroke:#AD1457,color:#880E4F
    classDef owasp fill:#E8EAF6,stroke:#283593,color:#1A237E
    classDef stage fill:#FFF8E1,stroke:#F57F17,color:#E65100

    subgraph TOOLS["Security Tools"]
        TH["TruffleHog"]:::tool
        GL["GitLeaks"]:::tool
        BD["Bandit"]:::tool
        SG["Semgrep"]:::tool
        PA["pip-audit"]:::tool
        TF["Trivy FS"]:::tool
        TI["Trivy Image"]:::tool
        CK["Checkov"]:::tool
        ZP["OWASP ZAP"]:::tool
    end

    subgraph STAGES["Pipeline Stages"]
        SS["Secret Scan"]:::stage
        SAST["SAST"]:::stage
        SCA["SCA"]:::stage
        CS["Container Scan"]:::stage
        IAC["IaC Scan"]:::stage
        DAST["DAST"]:::stage
    end

    subgraph OWASP["OWASP Top 10 2021"]
        A01["A01 Access Control"]:::owasp
        A02["A02 Crypto Failures"]:::owasp
        A03["A03 Injection"]:::owasp
        A05["A05 Misconfig"]:::owasp
        A06["A06 Vulnerable Deps"]:::owasp
        A07["A07 Auth Failures"]:::owasp
        A09["A09 Logging Failures"]:::owasp
        A10["A10 SSRF"]:::owasp
    end

    TH --> SS
    GL --> SS
    SS --> A02

    BD --> SAST
    SG --> SAST
    SAST --> A01
    SAST --> A03
    SAST --> A07

    PA --> SCA
    TF --> SCA
    SCA --> A06

    TI --> CS
    CS --> A06
    CS --> A05

    CK --> IAC
    IAC --> A05

    ZP --> DAST
    DAST --> A01
    DAST --> A03
    DAST --> A05
    DAST --> A09
    DAST --> A10
```

### Workflow Files

| Workflow | App | Target Cloud | Image Registry |
|---|---|---|---|
| [`devsecops-fastapi-user-eks.yml`](.github/workflows/devsecops-fastapi-user-eks.yml)   | USER  | AWS EKS   | ECR |
| [`devsecops-fastapi-admin-eks.yml`](.github/workflows/devsecops-fastapi-admin-eks.yml) | ADMIN | AWS EKS   | ECR |
| [`devsecops-fastapi-user-gke.yml`](.github/workflows/devsecops-fastapi-user-gke.yml)   | USER  | GCP GKE   | Artifact Registry |
| [`devsecops-fastapi-admin-gke.yml`](.github/workflows/devsecops-fastapi-admin-gke.yml) | ADMIN | GCP GKE   | Artifact Registry |
| [`devsecops-fastapi-user-aks.yml`](.github/workflows/devsecops-fastapi-user-aks.yml)   | USER  | Azure AKS | Azure ACR |
| [`devsecops-fastapi-admin-aks.yml`](.github/workflows/devsecops-fastapi-admin-aks.yml) | ADMIN | Azure AKS | Azure ACR |
| [`trivy-scan.yaml`](.github/workflows/trivy-scan.yaml) | (standalone) | — | — |

Supporting workflows (sources in [`actions/`](actions/), deployed to `.github/workflows/`):

| Workflow | Trigger | Purpose |
|---|---|---|
| [`reusable-security-scans.yml`](actions/reusable-security-scans.yml) | `workflow_call` | Shared secret-scan / SAST / SCA / IaC stages — one implementation for all (app × cloud) pipelines |
| [`ai-code-review.yml`](actions/ai-code-review.yml) | every PR | Claude security-first code review, inline comments (advisory) |
| [`ai-security-triage.yml`](actions/ai-security-triage.yml) | nightly + manual | Claude triages open code-scanning alerts → job summary + rolling issue |
| [`synthetic-monitor.yml`](actions/synthetic-monitor.yml) | every 10 min | Black-box `/healthz` probe of deployed apps → Slack on failure |

---

## Security Hardening — JWT, Sessions & Rate Limiting

The auth layer closes every token-handling finding from the external analysis ([ADR-0002](docs/adr/0002-jwt-rs256-rotation-revocation.md)):

| Control | Before | Now |
|---|---|---|
| Signing | HS256, one static `SECRET_KEY` shared by every service | **RS256 keypair** via `JWT_PRIVATE_KEY(_FILE)` / `JWT_PUBLIC_KEY(_FILE)` (e.g. the Secrets Store CSI mount); verifiers hold only the public key; HS256 survives solely as a warned local-dev fallback |
| Refresh tokens | Valid 7 days, replayable | **Rotation-on-use with families** — each `/auth/refresh` invalidates the presented token and issues a new one; replaying a rotated token is treated as theft and revokes the entire family |
| Logout / revocation | Client-side cookie delete only | **Server-side `jti` denylist** — logout revokes the access token and refresh family; every `decode_token` checks the denylist |
| Rate limiting | In-process (200/min × replica count) | **Globally enforced via Redis** (`REDIS_URL`) — 200/min general, 10/min auth endpoints, across all replicas; in-process fallback for dev |
| Cookies | `secure=False` | Secure + HttpOnly + SameSite by default (`COOKIE_SECURE=0` opt-out for local HTTP) |
| CORS | Wildcard origin **with** credentials | Env-driven allowlist (`CORS_ALLOW_ORIGINS`); credentials disabled under wildcard |

Shared token state lives in `token_store.py` (both apps, kept in lockstep): Redis-backed when `REDIS_URL` is set, thread-safe in-process otherwise.

---

## Observability & SRE

The Prometheus/Grafana/RabbitMQ operators were already installed; the **practice** that makes them useful is now committed to the repo:

- **SLOs** — [`docs/slo.md`](docs/slo.md): 99.5% availability, p95 < 500 ms, with an explicit error-budget policy (feature freeze on exhaustion).
- **Alert rules** — [`kubernetes/observability/prometheus-rules.yaml`](kubernetes/observability/prometheus-rules.yaml): multi-window multi-burn-rate availability alerts (14.4× page / 3× ticket), latency, outage, crash-loop, and auth-abuse (429 spike) rules, routed to Slack via a committed `AlertmanagerConfig`.
- **Dashboard** — [`kubernetes/observability/grafana-dashboard.yaml`](kubernetes/observability/grafana-dashboard.yaml): golden signals + SLO overlays, reconciled by the grafana-operator (dashboard-as-code, not click-ops).
- **App instrumentation** — `telemetry.py` in both apps: Prometheus `/metrics` (scraped via the committed [`ServiceMonitor`](kubernetes/observability/servicemonitor.yaml)), optional OpenTelemetry tracing (`OTEL_EXPORTER_OTLP_ENDPOINT`), structured JSON logs (`LOG_FORMAT=json`), and a dependency-free `/healthz`.
- **Synthetic monitoring** — [`actions/synthetic-monitor.yml`](actions/synthetic-monitor.yml) probes the public endpoints every 10 minutes from outside the cluster, catching LB/DNS/cert failures in-cluster probes can't see.

---

## Governance & Compliance

Previously the lowest-scoring domain (2.4/5) — now fully papered:

| Area | Where |
|---|---|
| Vulnerability disclosure | [`SECURITY.md`](SECURITY.md) — private advisories, 2-day ack / 7-day triage SLA |
| Review authority | [`.github/CODEOWNERS`](.github/CODEOWNERS) — per-path owners, security-sensitive paths overlap |
| Contribution rules | [`CONTRIBUTING.md`](CONTRIBUTING.md) + PR template with a mandatory security-impact statement + issue forms |
| Architecture decisions | [`docs/adr/`](docs/adr/) — GitOps sole applier, JWT hardening, Kyverno, service-mesh deferral, AI-native DevSecOps |
| Incident response | [`docs/governance/incident-response.md`](docs/governance/incident-response.md) — severities, roles, security addendum, blameless postmortems |
| Disaster recovery | [`docs/governance/disaster-recovery.md`](docs/governance/disaster-recovery.md) — **RTO/RPO per component**, three recovery scenarios, drill cadence |
| Data classification | [`docs/governance/data-classification.md`](docs/governance/data-classification.md) — Secret/PII/internal/public classes, PII inventory & flows |
| Audit-log retention | [`docs/governance/audit-log-retention.md`](docs/governance/audit-log-retention.md) — per-log retention incl. `user_info` (400 days, then anonymized) |
| Branching & protection | [`docs/governance/branching-strategy.md`](docs/governance/branching-strategy.md) — trunk-based, required checks per gate |
| Dependency currency | [`renovate.json`](renovate.json) — grouped update PRs, pinned action digests, prioritized vulnerability alerts |
| Releases | [`CHANGELOG.md`](CHANGELOG.md) (Keep-a-Changelog + SemVer) |

The finding-by-finding closure map for the whole external analysis lives in [`docs/gap-closure.md`](docs/gap-closure.md).

---

## AI-Native DevSecOps

The modernization layer ([ADR-0005](docs/adr/0005-ai-native-devsecops.md)) — AI drafts, ranks and proposes; **humans merge, deploy and remediate**:

| Capability | Entry point | How it runs |
|---|---|---|
| Agentic restore workflow | [`lib/agent_orchestrator.py`](dockerized/USER_FASTAPI/lib/agent_orchestrator.py) | In-app LangGraph ReAct agent (Claude) — `POST /agent/restore-workflow` |
| SARIF triage agent | [`ai/triage/sarif_triage.py`](ai/triage/sarif_triage.py) | Nightly: pulls open code-scanning alerts, dedupes across tools/apps, ranks by real exploitability, proposes fixes → job summary + rolling issue |
| AI code review | [`actions/ai-code-review.yml`](actions/ai-code-review.yml) | Claude Code action on every PR — security-first checklist, inline comments |
| AI runbooks & postmortems | [`ai/runbooks/generate_runbook.py`](ai/runbooks/generate_runbook.py) | CLI — drafts blameless postmortems from incident logs and per-alert runbooks in the house format |
| MCP server | [`ai/mcp/devsecops_mcp_server.py`](ai/mcp/devsecops_mcp_server.py) + [`.mcp.json`](.mcp.json) | Read-only bridge for Claude Code/Desktop: security posture, alerts, pipeline runs, deployment state, governance docs |
| Shift-left hooks | [`.pre-commit-config.yaml`](.pre-commit-config.yaml) | GitLeaks + Bandit + private-key detection at the developer keyboard |

Setup and usage examples: [`ai/README.md`](ai/README.md). CI needs the `ANTHROPIC_API_KEY` secret; its absence degrades gracefully (AI jobs fail independently of the security gates).

---

## Getting Started

### Prerequisites

- Docker & Docker Compose
- Python 3.9+
- AWS credentials configured (`~/.aws/credentials` or environment variables)
- PostgreSQL (or use the included DB container)

### Run with Docker

```bash
# Build and start all services (USER app, ADMIN app, PostgreSQL)
cd dockerized

# USER app (HTTPS on port 50443)
docker build -t fastapi-user ./USER
docker run -p 50443:50443 --env-file USER/env.sh fastapi-user

# ADMIN app (HTTPS on port 30443)
docker build -t flask-admin ./ADMIN
docker run -p 30443:30443 --env-file ADMIN/env.sh flask-admin
```

### Environment Variables

Both apps expect these variables (see `env.sh` in each app directory):

```bash
DB_HOST=<postgres-host>
DB_PORT=5432
DB_NAME=flaskapp
DB_USER=<db-user>
DB_PASSWORD=<db-password>
AWS_DEFAULT_REGION=us-east-1
AWS_ACCESS_KEY_ID=<key>
AWS_SECRET_ACCESS_KEY=<secret>
SECRET_KEY=<jwt-secret>
```

USER_FASTAPI additionally needs these to enable `/agent/restore-workflow` (see [`docs/github-secrets.md`](docs/github-secrets.md)):

```bash
ANTHROPIC_API_KEY=<claude-api-key>
ANTHROPIC_MODEL=claude-sonnet-5  # optional, defaults to claude-sonnet-5
```

Both FastAPI apps also honor these hardening/observability variables (all optional; safe defaults):

```bash
# JWT — RS256 in production (falls back to HS256 + SECRET_KEY with a warning)
JWT_PRIVATE_KEY=<PEM>            # or JWT_PRIVATE_KEY_FILE=/mnt/secrets-store/jwt-private
JWT_PUBLIC_KEY=<PEM>             # or JWT_PUBLIC_KEY_FILE=/mnt/secrets-store/jwt-public

# Server-side token state + global rate limits (per-pod in-process without it)
REDIS_URL=redis://redis.fastapi-namespace:6379/0

# Web security
COOKIE_SECURE=1                  # set 0 only for local HTTP development
CORS_ALLOW_ORIGINS=https://app.example.com,https://admin.example.com

# Observability
ENABLE_METRICS=1                 # Prometheus /metrics (set 0 to disable)
LOG_FORMAT=json                  # structured JSON logs
OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4318   # enables tracing when set
OTEL_SERVICE_NAME=fastapi-user-app
```

### Initialize the Database

```bash
psql -h <host> -U <user> -d flaskapp -f dockerized/DB/schema/flaskapp.sql
```

---

## Usage — cURL Examples

### Restore a DB from Snapshot

```bash
#!/bin/bash
# Restore RDS instance from snapshot

snapshotname=${1}   # e.g. my-snapshot-name
endpoint=${2}       # e.g. myDB.cluster-XXXYYY.us-east-1.rds.amazonaws.com

EMAIL=$(cat ~/.password/mySecrets2 | grep email | awk '{print $2}')
PASSWORD=$(cat ~/.password/mySecrets2 | grep password | awk '{print $2}')

# Login (stores JWT cookie)
curl -k "https://192.168.2.15:50443/login" \
    --data-urlencode "email=${EMAIL}" \
    --data-urlencode "password=${PASSWORD}" \
    --cookie-jar cookies.txt --verbose > login_log.html

# Trigger restore
curl -k "https://192.168.2.15:50443/restore" \
    --data-urlencode "snapshotname=${snapshotname}" \
    --data-urlencode "endpoint=${endpoint}" \
    --cookie cookies.txt --cookie-jar cookies.txt --verbose
    echo

rm -f cookies.txt
```

### Check Restore Status

```bash
#!/bin/bash
snapshotname=${1}
endpoint=${2}

EMAIL=$(cat ~/.password/mySecrets2 | grep email | awk '{print $2}')
PASSWORD=$(cat ~/.password/mySecrets2 | grep password | awk '{print $2}')

curl -k "https://192.168.2.15:50443/login" \
    --data-urlencode "email=${EMAIL}" \
    --data-urlencode "password=${PASSWORD}" \
    --cookie-jar cookies.txt --verbose > login_log.html

curl -k "https://192.168.2.15:50443/status" \
    --data-urlencode "snapshotname=${snapshotname}" \
    --data-urlencode "endpoint=${endpoint}" \
    --cookie cookies.txt --cookie-jar cookies.txt --verbose
    echo

rm -f cookies.txt
```

### Attach DB Instance to Cluster

```bash
#!/bin/bash
endpoint=${1}       # e.g. myDB.cluster-XXXYYY.us-east-1.rds.amazonaws.com
instanceclass=${2}  # e.g. db.t3.medium

EMAIL=$(cat ~/.password/mySecrets2 | grep email | awk '{print $2}')
PASSWORD=$(cat ~/.password/mySecrets2 | grep password | awk '{print $2}')

curl -k "https://192.168.2.15:50443/login" \
    --data-urlencode "email=${EMAIL}" \
    --data-urlencode "password=${PASSWORD}" \
    --cookie-jar cookies.txt --verbose > login_log.html

curl -k "https://192.168.2.15:50443/attachdb" \
    --data-urlencode "endpoint=${endpoint}" \
    --data-urlencode "instanceclass=${instanceclass}" \
    --cookie cookies.txt --cookie-jar cookies.txt --verbose
    echo

rm -f cookies.txt
```

### Run the Agentic Restore Workflow

```bash
#!/bin/bash
# Restore + status + optional attach + notify, planned and executed by the
# LangGraph agent in a single call. Requires ANTHROPIC_API_KEY to be set on
# the running USER_FASTAPI container.

snapshotname=${1}    # e.g. my-snapshot-name
endpoint=${2}        # e.g. myDB.cluster-XXXYYY.us-east-1.rds.amazonaws.com
instanceclass=${3}   # optional — attach a reader once restored, e.g. db.r5.large

EMAIL=$(cat ~/.password/mySecrets2 | grep email | awk '{print $2}')
PASSWORD=$(cat ~/.password/mySecrets2 | grep password | awk '{print $2}')

curl -k "https://192.168.2.15:50443/login" \
    --data-urlencode "email=${EMAIL}" \
    --data-urlencode "password=${PASSWORD}" \
    --cookie-jar cookies.txt --verbose > login_log.html

curl -k "https://192.168.2.15:50443/agent/restore-workflow" \
    --data-urlencode "snapshotname=${snapshotname}" \
    --data-urlencode "endpoint=${endpoint}" \
    --data-urlencode "instanceclass=${instanceclass}" \
    --data-urlencode "goal=Restore this snapshot and attach a reader once it's ready." \
    --cookie cookies.txt --cookie-jar cookies.txt --verbose
    echo

rm -f cookies.txt
```

---

## Screenshots

Sign Up page:

![Alt text](images/signup.png)

Sign In page:

![Alt text](images/signin.png)

RestoreDB page:

![Alt text](images/restore.png)

RestoreDB Status page:

![Alt text](images/restore_status.png)

AttachDB page 1:

![Alt text](images/attachdb1.png)

AttachDB page 2:

![Alt text](images/attachdb2.png)

DB Restore Options after login:

![Alt text](images/db_restore_options_after_login.png)

---

## Contact

###### skondla.ai@gmail.com

###### DevSecOps Blog Posts

[DevSecOps — Deploying WebApp on Azure AKS cluster with Github Actions](https://kondlawork.medium.com/devsecops-deploying-webapp-on-azure-aks-cluster-with-github-actions-efc72bdc552a)

[DevSecOps — Deploying WebApp on AWS EKS cluster with Github Actions](https://kondlawork.medium.com/devsecops-deploying-webapp-on-aws-eks-cluster-with-github-actions-da8865a1b27)

[DevSecOps — Deploying WebApp on Google Cloud GKE cluster with Github Actions](https://medium.com/@kondlawork/devsecops-deploying-webapp-on-google-cloud-gke-cluster-with-github-actions-1028c0630dde)
