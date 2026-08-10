# SMI Production Deployment Guide

## Prerequisites

- PostgreSQL 14+ cluster with HA (primary + 2 replicas)
- PgBouncer or connection pooling configured
- AWS Secrets Manager or HashiCorp Vault for secret management
- Kubernetes cluster OR Docker Swarm for orchestration
- Prometheus + Grafana for monitoring
- ELK Stack or Datadog for centralized logging

## Step-by-Step Deployment

### 1. Prepare Secrets

```bash
# Generate JWT RS256 keys
openssl genrsa -out /etc/oap/keys/private.pem 2048
openssl rsa -in /etc/oap/keys/private.pem -pubout -out /etc/oap/keys/public.pem

# Store in Secrets Manager
aws secretsmanager create-secret \
  --name oap/human-token \
  --secret-string "$(openssl rand -base64 32)"

aws secretsmanager create-secret \
  --name oap/approval-secret \
  --secret-string "$(openssl rand -base64 64)"
```

### 2. Configure Environment

```bash
# .env.production
OAP_ENV=production
OAP_SMI_DB=postgresql://user:password@postgres.example.com:5432/oap_smi_prod
OAP_HUMAN_TOKEN=$(aws secretsmanager get-secret-value --secret-id oap/human-token --query SecretString --output text)
OAP_APPROVAL_SECRET=$(aws secretsmanager get-secret-value --secret-id oap/approval-secret --query SecretString --output text)
OAP_APPROVAL_TTL_SECONDS=900
OAP_INTELLIGENCE_WORLDS=world-alpha,world-beta,world-gamma,world-delta,world-epsilon,world-zeta
OAP_CORS_ORIGINS=https://app.example.com,https://admin.example.com
JWT_PRIVATE_KEY_PATH=/etc/oap/keys/private.pem
JWT_PUBLIC_KEY_PATH=/etc/oap/keys/public.pem
```

### 3. Run Database Migrations

```bash
alembic upgrade head
```

### 4. Deploy Application

**Kubernetes**:
```bash
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/ingress.yaml
```

**Docker Swarm**:
```bash
docker stack deploy -c docker-compose.prod.yml oap-smi
```

### 5. Verify Deployment

```bash
# Check health
curl https://app.example.com/health

# Verify audit chain
curl -H "X-OAP-Human-Token: $OAP_HUMAN_TOKEN" \
     https://app.example.com/audit/verify

# Test approval flow
curl -X POST https://app.example.com/run \
  -H "Content-Type: application/json" \
  -d '{"message": "Test approval", "requires_execution": true}'
```

---

## Troubleshooting

### Database Connection Failures

```bash
# Check PostgreSQL connectivity
psql postgresql://user:password@host:5432/oap_smi_prod -c "SELECT 1"

# Verify PgBouncer
psql -h localhost -p 6432 -U user oap_smi_prod -c "SELECT 1"
```

### Audit Chain Breaks

```bash
# Verify chain integrity
curl -H "X-OAP-Human-Token: $TOKEN" https://app.example.com/audit/verify

# Check for tampering
select event_id, event_hash from audit_events order by sequence desc limit 10;
```

### Approval Timeouts

```bash
# Check pending approvals
select * from human_approvals where decision = 'PENDING';

# Extend timeout (if needed)
update human_approvals set expires_at = NOW() + interval '30 minutes' where approval_id = 'APR-xxx';
```
