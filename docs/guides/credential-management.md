# Credential Management Guide

Best practices for storing and managing API keys and credentials with GAO-Dev.

## Table of Contents

- [Storage Options](#storage-options)
- [Environment-Specific Recommendations](#environment-specific-recommendations)
- [Security Best Practices](#security-best-practices)
- [Credential Rotation](#credential-rotation)
- [Troubleshooting](#troubleshooting)

## Storage Options

GAO-Dev supports multiple methods for credential storage, each with different security and convenience trade-offs.

### Option 1: Environment Variables (Recommended for Production)

**Pros:**
- Industry standard
- Works with all deployment methods
- Easy to rotate
- Supported by all secret managers

**Cons:**
- Visible in process listings
- Must be set each session (unless in profile)

**Setup:**
```bash
# Linux/macOS - Add to ~/.bashrc or ~/.zshrc
export ANTHROPIC_API_KEY=sk-ant-api03-your-key-here

# Windows - Set system environment variable
setx ANTHROPIC_API_KEY "sk-ant-api03-your-key-here"
```

### Option 2: .env File (Recommended for Development)

**Pros:**
- Convenient for development
- Project-specific
- Automatically loaded by GAO-Dev

**Cons:**
- Risk of accidental commit
- Plain text on disk

**Setup:**
```bash
# Create .env file in project root
echo "ANTHROPIC_API_KEY=sk-ant-api03-your-key-here" >> .env

# Secure file permissions (Linux/macOS)
chmod 600 .env

# Verify .env is gitignored
grep ".env" .gitignore || echo ".env" >> .gitignore
```

### Option 3: System Keychain (Recommended for Desktop)

**Pros:**
- Encrypted at rest
- Integrated with OS security
- No plain text files

**Cons:**
- Requires additional setup
- Platform-specific

#### macOS Keychain

```bash
# Store credential
security add-generic-password -a "gao-dev" -s "ANTHROPIC_API_KEY" -w "sk-ant-..."

# Retrieve in script
export ANTHROPIC_API_KEY=$(security find-generic-password -a "gao-dev" -s "ANTHROPIC_API_KEY" -w)
```

#### Windows Credential Manager

```powershell
# Store credential (PowerShell)
cmdkey /generic:ANTHROPIC_API_KEY /user:gao-dev /pass:sk-ant-...

# Retrieve in script
$cred = Get-StoredCredential -Target "ANTHROPIC_API_KEY"
$env:ANTHROPIC_API_KEY = $cred.GetNetworkCredential().Password
```

#### Linux Secret Service (GNOME Keyring)

```bash
# Install secret-tool
sudo apt install libsecret-tools

# Store credential
echo -n "sk-ant-..." | secret-tool store --label="GAO-Dev API Key" service gao-dev key ANTHROPIC_API_KEY

# Retrieve in script
export ANTHROPIC_API_KEY=$(secret-tool lookup service gao-dev key ANTHROPIC_API_KEY)
```

### Option 4: Encrypted File

**Pros:**
- Portable
- Works offline
- Can be version controlled (encrypted)

**Cons:**
- Requires encryption key management
- Additional tooling needed

**Setup with SOPS:**
```bash
# Install SOPS
brew install sops  # macOS
# or
apt install sops   # Ubuntu

# Create encrypted secrets file
cat << EOF > secrets.yaml
anthropic_api_key: sk-ant-api03-your-key-here
openai_api_key: sk-your-key-here
EOF

# Encrypt with age key
sops -e -i secrets.yaml

# Use in scripts
export ANTHROPIC_API_KEY=$(sops -d --extract '["anthropic_api_key"]' secrets.yaml)
```

### Option 5: Secret Manager Services

For enterprise and production deployments.

#### AWS Secrets Manager

```bash
# Store secret
aws secretsmanager create-secret --name gao-dev/api-keys --secret-string '{"ANTHROPIC_API_KEY":"sk-ant-..."}'

# Retrieve
export ANTHROPIC_API_KEY=$(aws secretsmanager get-secret-value --secret-id gao-dev/api-keys --query SecretString --output text | jq -r '.ANTHROPIC_API_KEY')
```

#### HashiCorp Vault

```bash
# Store secret
vault kv put secret/gao-dev ANTHROPIC_API_KEY=sk-ant-...

# Retrieve
export ANTHROPIC_API_KEY=$(vault kv get -field=ANTHROPIC_API_KEY secret/gao-dev)
```

#### Azure Key Vault

```bash
# Store secret
az keyvault secret set --vault-name my-vault --name ANTHROPIC-API-KEY --value "sk-ant-..."

# Retrieve
export ANTHROPIC_API_KEY=$(az keyvault secret show --vault-name my-vault --name ANTHROPIC-API-KEY --query value -o tsv)
```

## Environment-Specific Recommendations

### Local Development

**Recommended: .env file**

```bash
# Quick setup
cp .env.example .env
# Edit .env with your keys
chmod 600 .env
```

**Why:** Convenient, project-specific, easy to switch between projects.

### CI/CD Pipelines

**Recommended: Pipeline secrets**

**GitHub Actions:**
```yaml
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run GAO-Dev
        env:
          AGENT_PROVIDER: claude-code
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
        run: |
          pip install -e .
          gao-dev health
```

**GitLab CI:**
```yaml
variables:
  AGENT_PROVIDER: claude-code
  ANTHROPIC_API_KEY: $ANTHROPIC_API_KEY

test:
  script:
    - pip install -e .
    - gao-dev health
```

**Why:** Secrets never appear in logs, easy rotation, audit trail.

### Docker Containers

**Recommended: Environment variables via secrets**

```yaml
# docker-compose.yml
services:
  gao-dev:
    image: gao-dev/gao-dev:latest
    environment:
      - ANTHROPIC_API_KEY_FILE=/run/secrets/anthropic_key
    secrets:
      - anthropic_key

secrets:
  anthropic_key:
    file: ./secrets/anthropic_api_key.txt
```

**Why:** Secrets mounted as files, not visible in inspect, follows Docker best practices.

### Kubernetes

**Recommended: Kubernetes Secrets + External Secrets Operator**

```yaml
# External secret that syncs from AWS Secrets Manager
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: gao-dev-secrets
spec:
  secretStoreRef:
    kind: ClusterSecretStore
    name: aws-secrets-manager
  target:
    name: gao-dev-secrets
  data:
    - secretKey: ANTHROPIC_API_KEY
      remoteRef:
        key: gao-dev/api-keys
        property: ANTHROPIC_API_KEY
```

**Why:** Automatic rotation, centralized management, audit logging.

### Shared/Team Environments

**Recommended: Secret manager with RBAC**

Use a secret manager (AWS, Azure, HashiCorp Vault) with:
- Per-user access controls
- Audit logging
- Automatic rotation
- Environment separation (dev/staging/prod)

## Security Best Practices

### Do's

1. **Use environment variables** - Standard, secure, supported everywhere
2. **Set file permissions** - `.env` files should be `chmod 600`
3. **Use `.gitignore`** - Always ignore credential files
4. **Rotate regularly** - Create new keys quarterly
5. **Monitor usage** - Check provider dashboards for anomalies
6. **Use different keys per environment** - Dev, staging, prod should have separate keys
7. **Audit access** - Know who has access to secrets
8. **Use secret scanning** - Enable GitHub secret scanning, TruffleHog, etc.

### Don'ts

1. **Never commit keys** - Even in private repos
2. **Don't share keys via chat** - Use secret manager invitations
3. **Don't use production keys in development** - Create separate keys
4. **Don't log credentials** - Ensure logging sanitizes secrets
5. **Don't hardcode keys** - Always use environment variables
6. **Don't store in plaintext in CI** - Use pipeline secrets feature

### Detecting Leaked Credentials

**Pre-commit hook:**
```bash
# Install detect-secrets
pip install detect-secrets

# Initialize baseline
detect-secrets scan > .secrets.baseline

# Add pre-commit hook
cat << EOF >> .pre-commit-config.yaml
repos:
  - repo: https://github.com/Yelp/detect-secrets
    rev: v1.4.0
    hooks:
      - id: detect-secrets
        args: ['--baseline', '.secrets.baseline']
EOF
```

**Git-secrets:**
```bash
# Install git-secrets
brew install git-secrets

# Configure for AWS/Anthropic patterns
git secrets --register-aws
git secrets --add 'sk-ant-[a-zA-Z0-9-]+'

# Scan repository
git secrets --scan
```

## Credential Rotation

### When to Rotate

- **Immediately:** After suspected compromise
- **Upon team changes:** When members leave
- **Regularly:** Every 90 days (quarterly)
- **After incidents:** Security events, breaches

### Rotation Process

1. **Generate new key** in provider dashboard
2. **Update all systems** with new key
3. **Test** that new key works
4. **Revoke old key** in provider dashboard
5. **Document** rotation in change log

### Automation

**GitHub Actions rotation workflow:**
```yaml
name: Rotate API Keys
on:
  schedule:
    - cron: '0 0 1 */3 *'  # Quarterly
  workflow_dispatch:

jobs:
  rotate:
    runs-on: ubuntu-latest
    steps:
      - name: Generate new key
        id: new-key
        run: |
          # Call provider API to generate new key
          NEW_KEY=$(curl -X POST https://api.anthropic.com/v1/keys ...)
          echo "::add-mask::$NEW_KEY"
          echo "new_key=$NEW_KEY" >> $GITHUB_OUTPUT

      - name: Update secret
        uses: actions/github-script@v6
        with:
          script: |
            await github.rest.actions.createOrUpdateRepoSecret({
              owner: context.repo.owner,
              repo: context.repo.repo,
              secret_name: 'ANTHROPIC_API_KEY',
              encrypted_value: process.env.NEW_KEY
            })
```

## Troubleshooting

### "API key not found"

**Cause:** Environment variable not set or not visible to GAO-Dev.

**Solution:**
```bash
# Check if variable is set
echo $ANTHROPIC_API_KEY

# Check .env file exists and has correct format
cat .env | grep ANTHROPIC

# Reload shell configuration
source ~/.bashrc  # or ~/.zshrc

# Restart terminal if needed
```

### "Invalid API key"

**Cause:** Key is malformed, expired, or from wrong provider.

**Solution:**
```bash
# Verify key format
# Anthropic: sk-ant-api03-...
# OpenAI: sk-...

# Check key is active in provider dashboard

# Regenerate if needed
```

### "Permission denied" on .env

**Cause:** File permissions too restrictive or wrong ownership.

**Solution:**
```bash
# Fix ownership
chown $(whoami) .env

# Fix permissions
chmod 600 .env
```

### Credentials appearing in logs

**Cause:** Debug logging or improper error handling.

**Solution:**
```bash
# Disable debug mode
export GAO_DEV_DEBUG=false

# Check for accidental logging in custom code
grep -r "api_key" --include="*.py" | grep -v "os.getenv"
```

---

**See Also:**
- [Environment Variables Reference](./environment-variables.md)
- [Troubleshooting Guide](../troubleshooting/common-errors.md)
- [Docker Deployment Guide](../getting-started/docker-deployment.md)

---

**Last Updated**: 2025-11-19
