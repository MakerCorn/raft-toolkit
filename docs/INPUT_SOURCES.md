# Input Sources Guide

The RAFT Toolkit supports multiple input sources for document processing, allowing you to process documents from local filesystems, cloud storage, and enterprise document repositories.

## Supported Input Sources

### 📁 Local Files
Process documents from local filesystem paths.

**Supported:**
- Single files or directories
- Recursive directory scanning
- All document types (PDF, TXT, JSON, PPTX)

**Configuration:**
```bash
# CLI
python raft.py --source-type local --datapath ./documents

# Environment
export RAFT_SOURCE_TYPE=local
export RAFT_DATAPATH=./documents
```

### ☁️ Amazon S3
Process documents directly from S3 buckets with full AWS authentication support.

**Supported:**
- S3 buckets and object prefixes
- AWS credential methods (access keys, IAM roles, profiles)
- Regional bucket support
- Large file handling with streaming

**Authentication Methods:**

#### 1. Environment Variables
```bash
export AWS_ACCESS_KEY_ID=your_access_key
export AWS_SECRET_ACCESS_KEY=your_secret_key
export AWS_DEFAULT_REGION=us-east-1

python raft.py --source-type s3 --source-uri s3://bucket/path/
```

#### 2. AWS Credentials File
```bash
# ~/.aws/credentials
[default]
aws_access_key_id = your_access_key
aws_secret_access_key = your_secret_key

python raft.py --source-type s3 --source-uri s3://bucket/path/
```

#### 3. IAM Roles (EC2/ECS/Lambda)
```bash
# No credentials needed when running on AWS with proper IAM role
python raft.py --source-type s3 --source-uri s3://bucket/path/
```

#### 4. CLI Credentials
```bash
python raft.py \
  --source-type s3 \
  --source-uri s3://bucket/path/ \
  --source-credentials '{"aws_access_key_id":"key","aws_secret_access_key":"secret","region_name":"us-east-1"}'
```

**S3 URI Formats:**
```bash
s3://bucket-name                    # Process entire bucket
s3://bucket-name/prefix/            # Process objects with prefix
s3://bucket-name/folder/subfolder/  # Process specific folder
```

### 🏢 SharePoint Online
Process documents from SharePoint Online document libraries with Azure AD authentication.

**Supported:**
- SharePoint Online sites and document libraries
- Multiple authentication methods
- Custom folder paths within libraries
- Office 365 file types

**Authentication Methods:**

#### 1. Client Credentials (Recommended for Production)
```bash
# Requires Azure AD app registration with SharePoint permissions
python raft.py \
  --source-type sharepoint \
  --source-uri "https://company.sharepoint.com/sites/mysite/Shared Documents" \
  --source-credentials '{
    "auth_method": "client_credentials",
    "client_id": "your_app_id",
    "client_secret": "your_app_secret",
    "tenant_id": "your_tenant_id"
  }'
```

#### 2. Device Code Flow (Interactive)
```bash
# Interactive authentication - user will be prompted to sign in
python raft.py \
  --source-type sharepoint \
  --source-uri "https://company.sharepoint.com/sites/mysite/Documents" \
  --source-credentials '{
    "auth_method": "device_code",
    "client_id": "your_app_id",
    "tenant_id": "your_tenant_id"
  }'
```

#### 3. Username/Password (Not Recommended)
```bash
# Only for testing - not recommended for production
python raft.py \
  --source-type sharepoint \
  --source-uri "https://company.sharepoint.com/sites/mysite/Documents" \
  --source-credentials '{
    "auth_method": "username_password",
    "client_id": "your_app_id",
    "tenant_id": "your_tenant_id",
    "username": "user@company.com",
    "password": "password"
  }'
```

**SharePoint URI Formats:**
```bash
# Document library root
https://company.sharepoint.com/sites/mysite/Shared Documents

# Specific folder
https://company.sharepoint.com/sites/mysite/Shared Documents/Projects

# Different document library
https://company.sharepoint.com/sites/mysite/Documents
```

## Configuration Options

### File Filtering

#### Include/Exclude Patterns
```bash
# Include specific patterns
--source-include-patterns '["**/*.pdf", "**/reports/*.txt", "**/2024/**"]'

# Exclude specific patterns  
--source-exclude-patterns '["**/temp/**", "**/.DS_Store", "**/draft*"]'

# Environment variables
export RAFT_SOURCE_INCLUDE_PATTERNS='["**/*.pdf"]'
export RAFT_SOURCE_EXCLUDE_PATTERNS='["**/temp/**"]'
```

#### File Size Limits
```bash
# Set maximum file size (in bytes)
--source-max-file-size 52428800  # 50MB

# Environment variable
export RAFT_SOURCE_MAX_FILE_SIZE=52428800
```

#### Supported Document Types
```bash
# Filter by document type
--doctype pdf    # Only PDF files
--doctype txt    # Only text files
--doctype json   # Only JSON files
--doctype pptx   # Only PowerPoint files
```

### Batch Processing
```bash
# Set batch size for processing
--source-batch-size 50

# Environment variable
export RAFT_SOURCE_BATCH_SIZE=50
```

## Setup Guides

### Setting Up S3 Access

#### Option 1: IAM User with Access Keys
1. Create IAM user in AWS Console
2. Attach policy with S3 read permissions:
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "s3:GetObject",
                "s3:ListBucket"
            ],
            "Resource": [
                "arn:aws:s3:::your-bucket-name",
                "arn:aws:s3:::your-bucket-name/*"
            ]
        }
    ]
}
```
3. Create access keys and configure credentials

#### Option 2: IAM Role (for EC2/ECS)
1. Create IAM role with S3 read permissions
2. Attach role to EC2 instance or ECS task
3. No additional configuration needed

### Setting Up SharePoint Access

#### Prerequisites
1. SharePoint Online subscription
2. Azure AD tenant admin access
3. Appropriate SharePoint site permissions

#### Azure AD App Registration
1. Go to Azure Portal > Azure Active Directory > App registrations
2. Click "New registration"
3. Configure:
   - **Name**: RAFT Toolkit SharePoint Access
   - **Supported account types**: Single tenant
   - **Redirect URI**: Leave blank for client credentials
4. Note the **Application (client) ID** and **Directory (tenant) ID**

#### API Permissions
1. Go to API permissions > Add a permission
2. Select **Microsoft Graph**
3. Add these permissions:
   - `Sites.Read.All` (Application permission)
   - `Files.Read.All` (Application permission)
4. Grant admin consent

#### Client Secret (for client credentials)
1. Go to Certificates & secrets
2. Click "New client secret"
3. Set expiration (recommended: 12-24 months)
4. Copy the secret value immediately

#### Device Code Flow Setup
1. Go to Authentication
2. Add platform > Mobile and desktop applications
3. Add redirect URI: `https://login.microsoftonline.com/common/oauth2/nativeclient`
4. Enable "Allow public client flows"

## Environment Variable Reference

### All Sources
```bash
# Core configuration
export RAFT_SOURCE_TYPE=local|s3|sharepoint
export RAFT_SOURCE_URI=path_or_uri
export RAFT_SOURCE_MAX_FILE_SIZE=52428800
export RAFT_SOURCE_BATCH_SIZE=100

# Filtering
export RAFT_SOURCE_INCLUDE_PATTERNS='["**/*.pdf"]'
export RAFT_SOURCE_EXCLUDE_PATTERNS='["**/temp/**"]'

# Rate Limiting (for cloud sources)
export RAFT_RATE_LIMIT_ENABLED=false
export RAFT_RATE_LIMIT_STRATEGY=fixed_window
export RAFT_RATE_LIMIT_PRESET=gpt-4
export RAFT_RATE_LIMIT_REQUESTS_PER_MINUTE=60
export RAFT_RATE_LIMIT_TOKENS_PER_MINUTE=90000
```

### S3 Specific
```bash
# AWS credentials
export AWS_ACCESS_KEY_ID=your_key
export AWS_SECRET_ACCESS_KEY=your_secret
export AWS_DEFAULT_REGION=us-east-1
export AWS_SESSION_TOKEN=token  # If using temporary credentials

# Or as JSON
export RAFT_SOURCE_CREDENTIALS='{
  "aws_access_key_id": "key",
  "aws_secret_access_key": "secret",
  "region_name": "us-east-1"
}'
```

### SharePoint Specific
```bash
# Client credentials
export RAFT_SOURCE_CREDENTIALS='{
  "auth_method": "client_credentials",
  "client_id": "app_id",
  "client_secret": "secret",
  "tenant_id": "tenant_id"
}'

# Device code
export RAFT_SOURCE_CREDENTIALS='{
  "auth_method": "device_code",
  "client_id": "app_id",
  "tenant_id": "tenant_id"
}'
```

## Validation and Testing

### Preview Mode
Test your source configuration without processing:
```bash
# Local
python raft.py --datapath ./docs --preview

# S3
python raft.py --source-type s3 --source-uri s3://bucket/path/ --preview

# SharePoint
python raft.py --source-type sharepoint --source-uri "https://company.sharepoint.com/sites/site/Documents" --source-credentials '...' --preview

# With rate limiting
python raft.py --source-type s3 --source-uri s3://bucket/path/ --rate-limit --rate-limit-preset gpt-4 --preview

# With custom templates
python raft.py --datapath ./docs --embedding-prompt-template ./templates/custom_embedding.txt --preview
```

### Validation Mode
Validate configuration and connectivity:
```bash
# Validate any source type
python raft.py [source options] --validate
```

### Test Commands
```bash
# Test local access
python raft.py --datapath ./test_docs --doctype pdf --validate

# Test S3 access
python raft.py \
  --source-type s3 \
  --source-uri s3://test-bucket/ \
  --validate

# Test SharePoint access
python raft.py \
  --source-type sharepoint \
  --source-uri "https://company.sharepoint.com/sites/test/Shared Documents" \
  --source-credentials '{"auth_method":"device_code","client_id":"app_id","tenant_id":"tenant_id"}' \
  --validate

# Test with rate limiting
python raft.py \
  --source-type s3 \
  --source-uri s3://test-bucket/ \
  --rate-limit \
  --rate-limit-strategy adaptive \
  --validate

# Test with LangWatch integration
python raft.py \
  --datapath ./test_docs \
  --langwatch-enabled \
  --langwatch-project test-project \
  --validate
```

## Troubleshooting

### Common Issues

#### S3 Access Denied
```bash
# Check bucket permissions
aws s3 ls s3://your-bucket-name --profile your-profile

# Verify credentials
aws sts get-caller-identity --profile your-profile
```

#### SharePoint Authentication Errors
1. **Invalid client_id**: Verify app registration exists and client ID is correct
2. **Insufficient permissions**: Ensure API permissions are granted and admin consent given
3. **Tenant not found**: Verify tenant ID is correct
4. **Site not accessible**: Check SharePoint site URL and permissions

#### General Issues
1. **Network connectivity**: Ensure network access to AWS/Microsoft services
2. **Firewall/proxy**: Configure proxy settings if required
3. **Credentials expiry**: Check if credentials/secrets have expired
4. **File permissions**: Ensure sufficient permissions to read files

### Debug Mode
Enable verbose logging for troubleshooting:
```bash
# Basic debug logging
export RAFT_LOG_LEVEL=DEBUG
python raft.py [options]

# With structured logging
export ENABLE_STRUCTURED_LOGGING=true
export LOG_FORMAT=json
python raft.py [options]

# With LangWatch tracing
export LANGWATCH_ENABLED=true
export LANGWATCH_DEBUG=true
python raft.py [options]

# With distributed tracing
export ENABLE_TRACING=true
export JAEGER_ENDPOINT=http://localhost:14268/api/traces
python raft.py [options]
```

### Support
For additional support:
1. Check the main [README.md](../README.md) for general documentation
2. Review [CONFIGURATION.md](CONFIGURATION.md) for configuration options
3. See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for common issues
4. Create an issue in the project repository