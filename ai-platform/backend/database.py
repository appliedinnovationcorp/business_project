from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import boto3
import json
import os
from dotenv import load_dotenv

load_dotenv()

def get_database_url():
    """Get database URL from AWS Secrets Manager"""
    try:
        # Get secret from AWS Secrets Manager
        secrets_client = boto3.client('secretsmanager', region_name=os.getenv('AWS_REGION', 'us-east-1'))
        secret_arn = os.getenv('DB_SECRET_ARN')
        
        if not secret_arn:
            raise ValueError("DB_SECRET_ARN environment variable not set")
        
        response = secrets_client.get_secret_value(SecretId=secret_arn)
        secret = json.loads(response['SecretString'])
        
        # Construct database URL
        database_url = f"postgresql://{secret['username']}:{secret['password']}@{secret['host']}:{secret['port']}/{secret['dbname']}"
        return database_url
    
    except Exception as e:
        print(f"Error getting database credentials: {e}")
        # Fallback to local development database
        return "postgresql://postgres:password@localhost:5432/aiplatform"

# Database configuration
DATABASE_URL = get_database_url()

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    """Database dependency"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
