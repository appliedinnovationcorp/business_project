# AWS Infrastructure Setup Guide

**Date:** July 4, 2025  
**Purpose:** Step-by-step guide for setting up AWS infrastructure and development environment

## Phase 1: AWS Account Setup & Security

### 1. AWS Account Creation
```bash
# If you don't have an AWS account yet:
# 1. Go to https://aws.amazon.com/
# 2. Click "Create an AWS Account"
# 3. Follow the registration process
# 4. Add payment method (you'll stay within free tier initially)
```

### 2. Enable MFA and Create IAM User
```bash
# Install AWS CLI
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

# Verify installation
aws --version
```

**Security Setup Commands:**
```bash
# Configure AWS CLI with your credentials
aws configure

# Create IAM user for development (replace with your details)
aws iam create-user --user-name ai-platform-dev
aws iam create-access-key --user-name ai-platform-dev

# Attach necessary policies
aws iam attach-user-policy --user-name ai-platform-dev --policy-arn arn:aws:iam::aws:policy/PowerUserAccess
```

### 3. Set Up Development Environment
```bash
# Create project directory structure
mkdir -p ~/ai-platform/{frontend,backend,infrastructure,docs}
cd ~/ai-platform

# Initialize Git repository
git init
echo "node_modules/\n.env\n*.log\ndist/\nbuild/" > .gitignore
```

## Phase 2: Core Infrastructure Setup

### 1. VPC and Networking
```bash
# Create VPC using AWS CLI
aws ec2 create-vpc --cidr-block 10.0.0.0/16 --tag-specifications 'ResourceType=vpc,Tags=[{Key=Name,Value=ai-platform-vpc}]'

# Get VPC ID (replace with actual ID from above command)
export VPC_ID=$(aws ec2 describe-vpcs --filters "Name=tag:Name,Values=ai-platform-vpc" --query 'Vpcs[0].VpcId' --output text)

# Create subnets
aws ec2 create-subnet --vpc-id $VPC_ID --cidr-block 10.0.1.0/24 --availability-zone us-east-1a --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=ai-platform-public-1a}]'
aws ec2 create-subnet --vpc-id $VPC_ID --cidr-block 10.0.2.0/24 --availability-zone us-east-1b --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=ai-platform-public-1b}]'
aws ec2 create-subnet --vpc-id $VPC_ID --cidr-block 10.0.3.0/24 --availability-zone us-east-1a --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=ai-platform-private-1a}]'
aws ec2 create-subnet --vpc-id $VPC_ID --cidr-block 10.0.4.0/24 --availability-zone us-east-1b --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=ai-platform-private-1b}]'
```

### 2. S3 Buckets for Storage
```bash
# Create S3 buckets (replace 'your-unique-prefix' with something unique)
aws s3 mb s3://your-unique-prefix-ai-platform-data
aws s3 mb s3://your-unique-prefix-ai-platform-models
aws s3 mb s3://your-unique-prefix-ai-platform-static
aws s3 mb s3://your-unique-prefix-ai-platform-backups

# Enable versioning on critical buckets
aws s3api put-bucket-versioning --bucket your-unique-prefix-ai-platform-data --versioning-configuration Status=Enabled
aws s3api put-bucket-versioning --bucket your-unique-prefix-ai-platform-models --versioning-configuration Status=Enabled
```

### 3. RDS Database Setup
```bash
# Create RDS subnet group
aws rds create-db-subnet-group \
    --db-subnet-group-name ai-platform-subnet-group \
    --db-subnet-group-description "Subnet group for AI platform database" \
    --subnet-ids subnet-xxx subnet-yyy  # Replace with your private subnet IDs

# Create RDS instance (PostgreSQL)
aws rds create-db-instance \
    --db-instance-identifier ai-platform-db \
    --db-instance-class db.t3.micro \
    --engine postgres \
    --master-username aiplatform \
    --master-user-password YourSecurePassword123! \
    --allocated-storage 20 \
    --db-subnet-group-name ai-platform-subnet-group \
    --vpc-security-group-ids sg-xxx  # Replace with your security group ID
```

## Phase 3: Development Tools Setup

### 1. Install Development Dependencies
```bash
# Install Node.js and npm
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs

# Install Python and pip
sudo apt-get update
sudo apt-get install -y python3 python3-pip python3-venv

# Install Docker
sudo apt-get install -y docker.io
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -aG docker $USER

# Install Terraform
wget -O- https://apt.releases.hashicorp.com/gpg | gpg --dearmor | sudo tee /usr/share/keyrings/hashicorp-archive-keyring.gpg
echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/hashicorp.list
sudo apt update && sudo apt install terraform
```

### 2. Set Up Development Environment
```bash
# Create Python virtual environment
cd ~/ai-platform/backend
python3 -m venv venv
source venv/bin/activate
pip install fastapi uvicorn sqlalchemy psycopg2-binary boto3 mlflow

# Initialize Node.js project
cd ~/ai-platform/frontend
npm init -y
npm install react react-dom next.js typescript @types/react @types/node
npm install -D tailwindcss postcss autoprefixer
```

### 3. Infrastructure as Code Setup
```bash
# Create Terraform configuration
cd ~/ai-platform/infrastructure
cat > main.tf << 'EOF'
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = "us-east-1"
}

# S3 bucket for Terraform state
resource "aws_s3_bucket" "terraform_state" {
  bucket = "your-unique-prefix-ai-platform-terraform-state"
}

resource "aws_s3_bucket_versioning" "terraform_state_versioning" {
  bucket = aws_s3_bucket.terraform_state.id
  versioning_configuration {
    status = "Enabled"
  }
}
EOF

# Initialize Terraform
terraform init
terraform plan
terraform apply
```

## Phase 4: CI/CD Pipeline Setup

### 1. GitHub Actions Workflow
```bash
# Create GitHub Actions workflow
mkdir -p ~/ai-platform/.github/workflows
cat > ~/ai-platform/.github/workflows/deploy.yml << 'EOF'
name: Deploy AI Platform

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - name: Set up Node.js
      uses: actions/setup-node@v3
      with:
        node-version: '18'
    - name: Install dependencies
      run: npm ci
      working-directory: ./frontend
    - name: Run tests
      run: npm test
      working-directory: ./frontend

  deploy:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
    - uses: actions/checkout@v3
    - name: Configure AWS credentials
      uses: aws-actions/configure-aws-credentials@v2
      with:
        aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
        aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
        aws-region: us-east-1
    - name: Deploy to AWS
      run: |
        # Add deployment commands here
        echo "Deploying to AWS..."
EOF
```

### 2. Environment Configuration
```bash
# Create environment configuration files
cat > ~/ai-platform/.env.example << 'EOF'
# AWS Configuration
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key

# Database Configuration
DATABASE_URL=postgresql://username:password@host:5432/database

# Application Configuration
NODE_ENV=development
PORT=3000
API_PORT=8000

# External Services
OPENAI_API_KEY=your_openai_key
STRIPE_SECRET_KEY=your_stripe_key
EOF

# Copy to actual .env file and fill in real values
cp ~/ai-platform/.env.example ~/ai-platform/.env
```

## Phase 5: Monitoring and Logging

### 1. CloudWatch Setup
```bash
# Create CloudWatch log groups
aws logs create-log-group --log-group-name /ai-platform/frontend
aws logs create-log-group --log-group-name /ai-platform/backend
aws logs create-log-group --log-group-name /ai-platform/workflows

# Create CloudWatch dashboard
aws cloudwatch put-dashboard --dashboard-name "AI-Platform-Dashboard" --dashboard-body '{
  "widgets": [
    {
      "type": "metric",
      "properties": {
        "metrics": [
          ["AWS/Lambda", "Duration", "FunctionName", "ai-platform-api"],
          ["AWS/Lambda", "Errors", "FunctionName", "ai-platform-api"]
        ],
        "period": 300,
        "stat": "Average",
        "region": "us-east-1",
        "title": "Lambda Performance"
      }
    }
  ]
}'
```

### 2. Security and Backup Setup
```bash
# Enable AWS Config for compliance monitoring
aws configservice put-configuration-recorder --configuration-recorder name=ai-platform-recorder,roleARN=arn:aws:iam::ACCOUNT-ID:role/config-role
aws configservice put-delivery-channel --delivery-channel name=ai-platform-channel,s3BucketName=your-config-bucket

# Set up automated backups
aws backup create-backup-plan --backup-plan '{
  "BackupPlanName": "ai-platform-backup-plan",
  "Rules": [
    {
      "RuleName": "daily-backup",
      "TargetBackupVault": "default",
      "ScheduleExpression": "cron(0 2 * * ? *)",
      "Lifecycle": {
        "DeleteAfterDays": 30
      }
    }
  ]
}'
```

## Cost Optimization Setup

### 1. AWS Budgets
```bash
# Create budget alert
aws budgets create-budget --account-id YOUR-ACCOUNT-ID --budget '{
  "BudgetName": "ai-platform-monthly-budget",
  "BudgetLimit": {
    "Amount": "100",
    "Unit": "USD"
  },
  "TimeUnit": "MONTHLY",
  "BudgetType": "COST"
}' --notifications-with-subscribers '[
  {
    "Notification": {
      "NotificationType": "ACTUAL",
      "ComparisonOperator": "GREATER_THAN",
      "Threshold": 80
    },
    "Subscribers": [
      {
        "SubscriptionType": "EMAIL",
        "Address": "your-email@example.com"
      }
    ]
  }
]'
```

### 2. Resource Tagging Strategy
```bash
# Create tagging policy
cat > ~/ai-platform/infrastructure/tags.tf << 'EOF'
locals {
  common_tags = {
    Project     = "ai-platform"
    Environment = "development"
    Owner       = "your-name"
    CostCenter  = "development"
  }
}

# Apply tags to all resources
resource "aws_default_tags" "default" {
  tags = local.common_tags
}
EOF
```

## Next Steps Checklist

- [ ] AWS account created and secured
- [ ] IAM user created with appropriate permissions
- [ ] VPC and networking configured
- [ ] S3 buckets created and configured
- [ ] RDS database instance launched
- [ ] Development environment set up locally
- [ ] Infrastructure as Code (Terraform) initialized
- [ ] CI/CD pipeline configured
- [ ] Monitoring and logging set up
- [ ] Cost management and budgets configured
- [ ] Security best practices implemented

## Estimated Monthly Costs (Development Phase)
- **RDS (db.t3.micro):** $15-20
- **S3 Storage:** $5-10
- **Lambda:** $0-5 (within free tier)
- **CloudWatch:** $5-10
- **Data Transfer:** $5-10
- **Total:** $30-55/month

This setup provides a solid foundation that can scale from development through production while maintaining cost efficiency and security best practices.
