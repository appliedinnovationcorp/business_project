import os
import json
import hashlib
import hmac
import time
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
from sqlalchemy import Column, Integer, String, Text, Boolean, JSON, DateTime, Float, ForeignKey
from sqlalchemy.orm import Session, relationship
import requests
import jwt

from models import Base, User

class IntegrationType(Enum):
    REST_API = "rest_api"
    WEBHOOK = "webhook"
    OAUTH = "oauth"
    GRAPHQL = "graphql"
    WEBSOCKET = "websocket"

class AuthenticationType(Enum):
    API_KEY = "api_key"
    OAUTH2 = "oauth2"
    BASIC_AUTH = "basic_auth"
    BEARER_TOKEN = "bearer_token"
    CUSTOM = "custom"

@dataclass
class APIEndpoint:
    method: str
    path: str
    description: str
    parameters: Dict[str, Any]
    response_schema: Dict[str, Any]
    rate_limit: Optional[int] = None
    requires_auth: bool = True

class ThirdPartyIntegration(Base):
    __tablename__ = "third_party_integrations"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    slug = Column(String, unique=True, nullable=False)
    description = Column(Text)
    provider = Column(String, nullable=False)  # salesforce, slack, github, etc.
    integration_type = Column(String, nullable=False)  # IntegrationType enum
    authentication_type = Column(String, nullable=False)  # AuthenticationType enum
    base_url = Column(String, nullable=False)
    documentation_url = Column(String)
    logo_url = Column(String)
    category = Column(String, nullable=False)  # crm, communication, development, etc.
    tags = Column(JSON, default=[])
    
    # Configuration
    config_schema = Column(JSON, nullable=False)  # JSON schema for configuration
    default_config = Column(JSON, default={})
    endpoints = Column(JSON, nullable=False)  # List of available endpoints
    webhook_config = Column(JSON, default={})  # Webhook configuration if applicable
    
    # Metadata
    version = Column(String, default="1.0.0")
    is_active = Column(Boolean, default=True)
    is_featured = Column(Boolean, default=False)
    popularity_score = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user_integrations = relationship("UserIntegration", back_populates="integration")
    workflow_integrations = relationship("WorkflowIntegration", back_populates="integration")

class UserIntegration(Base):
    __tablename__ = "user_integrations"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    integration_id = Column(Integer, ForeignKey("third_party_integrations.id"), nullable=False)
    
    # Configuration
    config = Column(JSON, nullable=False)  # User-specific configuration
    credentials = Column(JSON, nullable=False)  # Encrypted credentials
    webhook_url = Column(String)  # Generated webhook URL for this integration
    webhook_secret = Column(String)  # Secret for webhook verification
    
    # Status
    is_active = Column(Boolean, default=True)
    last_sync = Column(DateTime)
    sync_status = Column(String, default="pending")  # pending, success, error
    error_message = Column(Text)
    
    # Usage tracking
    total_requests = Column(Integer, default=0)
    last_request = Column(DateTime)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User")
    integration = relationship("ThirdPartyIntegration", back_populates="user_integrations")

class WorkflowIntegration(Base):
    __tablename__ = "workflow_integrations"
    
    id = Column(Integer, primary_key=True, index=True)
    workflow_id = Column(Integer, ForeignKey("workflows.id"), nullable=False)
    integration_id = Column(Integer, ForeignKey("third_party_integrations.id"), nullable=False)
    user_integration_id = Column(Integer, ForeignKey("user_integrations.id"), nullable=False)
    
    # Configuration for this specific workflow usage
    node_config = Column(JSON, nullable=False)  # Configuration for the workflow node
    mapping_config = Column(JSON, default={})  # Data mapping configuration
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    integration = relationship("ThirdPartyIntegration", back_populates="workflow_integrations")
    user_integration = relationship("UserIntegration")

class APIMarketplaceManager:
    """Manages third-party API integrations and marketplace"""
    
    def __init__(self):
        self.integrations = self._load_default_integrations()
    
    def _load_default_integrations(self) -> List[Dict[str, Any]]:
        """Load default third-party integrations"""
        return [
            self._get_salesforce_integration(),
            self._get_slack_integration(),
            self._get_github_integration(),
            self._get_office365_integration(),
            self._get_jira_integration(),
            self._get_hubspot_integration(),
            self._get_zapier_integration(),
        ]
    
    def _get_salesforce_integration(self) -> Dict[str, Any]:
        """Salesforce CRM integration"""
        return {
            'name': 'Salesforce',
            'slug': 'salesforce',
            'description': 'Integrate with Salesforce CRM to sync leads, contacts, and opportunities',
            'provider': 'Salesforce',
            'integration_type': IntegrationType.REST_API.value,
            'authentication_type': AuthenticationType.OAUTH2.value,
            'base_url': 'https://api.salesforce.com',
            'documentation_url': 'https://developer.salesforce.com/docs/api-explorer',
            'logo_url': 'https://cdn.aiplatform.com/integrations/salesforce.png',
            'category': 'crm',
            'tags': ['crm', 'sales', 'leads', 'contacts'],
            'config_schema': {
                'type': 'object',
                'properties': {
                    'instance_url': {'type': 'string', 'description': 'Salesforce instance URL'},
                    'api_version': {'type': 'string', 'default': 'v58.0'},
                    'sync_frequency': {'type': 'string', 'enum': ['real-time', 'hourly', 'daily'], 'default': 'hourly'}
                },
                'required': ['instance_url']
            },
            'endpoints': [
                {
                    'method': 'GET',
                    'path': '/services/data/v58.0/sobjects/Lead',
                    'description': 'Get leads',
                    'parameters': {'limit': 'integer', 'offset': 'integer'},
                    'response_schema': {'type': 'object'},
                    'rate_limit': 1000
                },
                {
                    'method': 'POST',
                    'path': '/services/data/v58.0/sobjects/Lead',
                    'description': 'Create lead',
                    'parameters': {'data': 'object'},
                    'response_schema': {'type': 'object'},
                    'rate_limit': 1000
                }
            ]
        }
    
    def _get_slack_integration(self) -> Dict[str, Any]:
        """Slack communication integration"""
        return {
            'name': 'Slack',
            'slug': 'slack',
            'description': 'Send notifications and messages to Slack channels',
            'provider': 'Slack Technologies',
            'integration_type': IntegrationType.WEBHOOK.value,
            'authentication_type': AuthenticationType.OAUTH2.value,
            'base_url': 'https://slack.com/api',
            'documentation_url': 'https://api.slack.com/',
            'logo_url': 'https://cdn.aiplatform.com/integrations/slack.png',
            'category': 'communication',
            'tags': ['messaging', 'notifications', 'team', 'collaboration'],
            'config_schema': {
                'type': 'object',
                'properties': {
                    'default_channel': {'type': 'string', 'description': 'Default channel for notifications'},
                    'mention_users': {'type': 'array', 'items': {'type': 'string'}},
                    'message_format': {'type': 'string', 'enum': ['plain', 'markdown'], 'default': 'markdown'}
                }
            },
            'endpoints': [
                {
                    'method': 'POST',
                    'path': '/chat.postMessage',
                    'description': 'Send message to channel',
                    'parameters': {'channel': 'string', 'text': 'string', 'attachments': 'array'},
                    'response_schema': {'type': 'object'},
                    'rate_limit': 100
                }
            ],
            'webhook_config': {
                'supported': True,
                'events': ['message', 'reaction_added', 'channel_created']
            }
        }
    
    def _get_github_integration(self) -> Dict[str, Any]:
        """GitHub repository integration"""
        return {
            'name': 'GitHub',
            'slug': 'github',
            'description': 'Integrate with GitHub repositories for code management and CI/CD',
            'provider': 'GitHub',
            'integration_type': IntegrationType.REST_API.value,
            'authentication_type': AuthenticationType.OAUTH2.value,
            'base_url': 'https://api.github.com',
            'documentation_url': 'https://docs.github.com/en/rest',
            'logo_url': 'https://cdn.aiplatform.com/integrations/github.png',
            'category': 'development',
            'tags': ['git', 'repository', 'code', 'ci-cd', 'version-control'],
            'config_schema': {
                'type': 'object',
                'properties': {
                    'default_repo': {'type': 'string', 'description': 'Default repository (owner/repo)'},
                    'branch': {'type': 'string', 'default': 'main'},
                    'auto_create_issues': {'type': 'boolean', 'default': False}
                }
            },
            'endpoints': [
                {
                    'method': 'GET',
                    'path': '/repos/{owner}/{repo}/issues',
                    'description': 'List repository issues',
                    'parameters': {'state': 'string', 'labels': 'string'},
                    'response_schema': {'type': 'array'},
                    'rate_limit': 5000
                },
                {
                    'method': 'POST',
                    'path': '/repos/{owner}/{repo}/issues',
                    'description': 'Create issue',
                    'parameters': {'title': 'string', 'body': 'string', 'labels': 'array'},
                    'response_schema': {'type': 'object'},
                    'rate_limit': 5000
                }
            ]
        }
    
    def _get_office365_integration(self) -> Dict[str, Any]:
        """Microsoft Office 365 integration"""
        return {
            'name': 'Microsoft 365',
            'slug': 'office365',
            'description': 'Integrate with Microsoft 365 for email, calendar, and document management',
            'provider': 'Microsoft',
            'integration_type': IntegrationType.REST_API.value,
            'authentication_type': AuthenticationType.OAUTH2.value,
            'base_url': 'https://graph.microsoft.com/v1.0',
            'documentation_url': 'https://docs.microsoft.com/en-us/graph/',
            'logo_url': 'https://cdn.aiplatform.com/integrations/office365.png',
            'category': 'productivity',
            'tags': ['email', 'calendar', 'documents', 'office', 'productivity'],
            'config_schema': {
                'type': 'object',
                'properties': {
                    'tenant_id': {'type': 'string', 'description': 'Azure AD tenant ID'},
                    'default_mailbox': {'type': 'string', 'description': 'Default mailbox for operations'},
                    'calendar_sync': {'type': 'boolean', 'default': True}
                },
                'required': ['tenant_id']
            },
            'endpoints': [
                {
                    'method': 'GET',
                    'path': '/me/messages',
                    'description': 'Get user messages',
                    'parameters': {'$filter': 'string', '$top': 'integer'},
                    'response_schema': {'type': 'object'},
                    'rate_limit': 10000
                },
                {
                    'method': 'POST',
                    'path': '/me/sendMail',
                    'description': 'Send email',
                    'parameters': {'message': 'object'},
                    'response_schema': {'type': 'object'},
                    'rate_limit': 10000
                }
            ]
        }
    
    def _get_jira_integration(self) -> Dict[str, Any]:
        """Atlassian Jira integration"""
        return {
            'name': 'Jira',
            'slug': 'jira',
            'description': 'Integrate with Jira for project management and issue tracking',
            'provider': 'Atlassian',
            'integration_type': IntegrationType.REST_API.value,
            'authentication_type': AuthenticationType.BASIC_AUTH.value,
            'base_url': 'https://{domain}.atlassian.net/rest/api/3',
            'documentation_url': 'https://developer.atlassian.com/cloud/jira/platform/rest/v3/',
            'logo_url': 'https://cdn.aiplatform.com/integrations/jira.png',
            'category': 'project-management',
            'tags': ['project-management', 'issues', 'tracking', 'agile'],
            'config_schema': {
                'type': 'object',
                'properties': {
                    'domain': {'type': 'string', 'description': 'Jira domain (without .atlassian.net)'},
                    'default_project': {'type': 'string', 'description': 'Default project key'},
                    'issue_type': {'type': 'string', 'default': 'Task'}
                },
                'required': ['domain']
            },
            'endpoints': [
                {
                    'method': 'GET',
                    'path': '/search',
                    'description': 'Search issues',
                    'parameters': {'jql': 'string', 'maxResults': 'integer'},
                    'response_schema': {'type': 'object'},
                    'rate_limit': 300
                },
                {
                    'method': 'POST',
                    'path': '/issue',
                    'description': 'Create issue',
                    'parameters': {'fields': 'object'},
                    'response_schema': {'type': 'object'},
                    'rate_limit': 300
                }
            ]
        }
    
    def _get_hubspot_integration(self) -> Dict[str, Any]:
        """HubSpot CRM integration"""
        return {
            'name': 'HubSpot',
            'slug': 'hubspot',
            'description': 'Integrate with HubSpot CRM for marketing and sales automation',
            'provider': 'HubSpot',
            'integration_type': IntegrationType.REST_API.value,
            'authentication_type': AuthenticationType.API_KEY.value,
            'base_url': 'https://api.hubapi.com',
            'documentation_url': 'https://developers.hubspot.com/docs/api/overview',
            'logo_url': 'https://cdn.aiplatform.com/integrations/hubspot.png',
            'category': 'crm',
            'tags': ['crm', 'marketing', 'sales', 'automation', 'contacts'],
            'config_schema': {
                'type': 'object',
                'properties': {
                    'portal_id': {'type': 'string', 'description': 'HubSpot portal ID'},
                    'default_pipeline': {'type': 'string', 'description': 'Default sales pipeline'},
                    'lead_scoring': {'type': 'boolean', 'default': True}
                }
            },
            'endpoints': [
                {
                    'method': 'GET',
                    'path': '/crm/v3/objects/contacts',
                    'description': 'Get contacts',
                    'parameters': {'limit': 'integer', 'properties': 'string'},
                    'response_schema': {'type': 'object'},
                    'rate_limit': 100
                },
                {
                    'method': 'POST',
                    'path': '/crm/v3/objects/contacts',
                    'description': 'Create contact',
                    'parameters': {'properties': 'object'},
                    'response_schema': {'type': 'object'},
                    'rate_limit': 100
                }
            ]
        }
    
    def _get_zapier_integration(self) -> Dict[str, Any]:
        """Zapier automation integration"""
        return {
            'name': 'Zapier',
            'slug': 'zapier',
            'description': 'Connect with 5000+ apps through Zapier automation platform',
            'provider': 'Zapier',
            'integration_type': IntegrationType.WEBHOOK.value,
            'authentication_type': AuthenticationType.API_KEY.value,
            'base_url': 'https://hooks.zapier.com/hooks/catch',
            'documentation_url': 'https://zapier.com/developer/documentation/v2/rest-hooks/',
            'logo_url': 'https://cdn.aiplatform.com/integrations/zapier.png',
            'category': 'automation',
            'tags': ['automation', 'workflow', 'integration', 'no-code'],
            'config_schema': {
                'type': 'object',
                'properties': {
                    'webhook_urls': {'type': 'array', 'items': {'type': 'string'}},
                    'trigger_events': {'type': 'array', 'items': {'type': 'string'}},
                    'data_format': {'type': 'string', 'enum': ['json', 'form'], 'default': 'json'}
                }
            },
            'endpoints': [
                {
                    'method': 'POST',
                    'path': '/{hook_id}',
                    'description': 'Send data to Zapier webhook',
                    'parameters': {'data': 'object'},
                    'response_schema': {'type': 'object'},
                    'rate_limit': 1000
                }
            ],
            'webhook_config': {
                'supported': True,
                'events': ['workflow_completed', 'data_processed', 'error_occurred']
            }
        }
    
    def initialize_default_integrations(self, db: Session):
        """Initialize default integrations in the database"""
        for integration_data in self.integrations:
            existing = db.query(ThirdPartyIntegration).filter(
                ThirdPartyIntegration.slug == integration_data['slug']
            ).first()
            
            if not existing:
                integration = ThirdPartyIntegration(**integration_data)
                db.add(integration)
        
        db.commit()
    
    def create_user_integration(self, db: Session, user_id: int, integration_slug: str, 
                              config: Dict[str, Any], credentials: Dict[str, Any]) -> UserIntegration:
        """Create a user integration"""
        integration = db.query(ThirdPartyIntegration).filter(
            ThirdPartyIntegration.slug == integration_slug
        ).first()
        
        if not integration:
            raise ValueError(f"Integration {integration_slug} not found")
        
        # Encrypt credentials (simplified - use proper encryption in production)
        encrypted_credentials = self._encrypt_credentials(credentials)
        
        # Generate webhook URL and secret if needed
        webhook_url = None
        webhook_secret = None
        if integration.integration_type == IntegrationType.WEBHOOK.value:
            webhook_secret = self._generate_webhook_secret()
            webhook_url = f"/api/webhooks/{integration.slug}/{user_id}/{webhook_secret}"
        
        user_integration = UserIntegration(
            user_id=user_id,
            integration_id=integration.id,
            config=config,
            credentials=encrypted_credentials,
            webhook_url=webhook_url,
            webhook_secret=webhook_secret
        )
        
        db.add(user_integration)
        db.commit()
        db.refresh(user_integration)
        
        # Test the integration
        self._test_integration(user_integration, db)
        
        return user_integration
    
    def execute_integration_request(self, user_integration: UserIntegration, 
                                  endpoint: str, method: str, data: Optional[Dict] = None) -> Dict[str, Any]:
        """Execute a request to a third-party integration"""
        integration = user_integration.integration
        credentials = self._decrypt_credentials(user_integration.credentials)
        
        # Build request URL
        base_url = integration.base_url
        if '{domain}' in base_url and 'domain' in user_integration.config:
            base_url = base_url.format(domain=user_integration.config['domain'])
        
        url = f"{base_url}{endpoint}"
        
        # Prepare headers
        headers = {'Content-Type': 'application/json'}
        
        # Add authentication
        if integration.authentication_type == AuthenticationType.API_KEY.value:
            headers['Authorization'] = f"Bearer {credentials.get('api_key')}"
        elif integration.authentication_type == AuthenticationType.OAUTH2.value:
            headers['Authorization'] = f"Bearer {credentials.get('access_token')}"
        elif integration.authentication_type == AuthenticationType.BASIC_AUTH.value:
            import base64
            auth_string = f"{credentials.get('username')}:{credentials.get('password')}"
            encoded_auth = base64.b64encode(auth_string.encode()).decode()
            headers['Authorization'] = f"Basic {encoded_auth}"
        
        # Make request
        try:
            if method.upper() == 'GET':
                response = requests.get(url, headers=headers, params=data)
            elif method.upper() == 'POST':
                response = requests.post(url, headers=headers, json=data)
            elif method.upper() == 'PUT':
                response = requests.put(url, headers=headers, json=data)
            elif method.upper() == 'DELETE':
                response = requests.delete(url, headers=headers)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            
            # Update usage tracking
            user_integration.total_requests += 1
            user_integration.last_request = datetime.utcnow()
            user_integration.sync_status = "success"
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            user_integration.sync_status = "error"
            user_integration.error_message = str(e)
            raise
    
    def handle_webhook(self, integration_slug: str, user_id: int, webhook_secret: str, 
                      payload: Dict[str, Any], headers: Dict[str, str]) -> Dict[str, Any]:
        """Handle incoming webhook from third-party integration"""
        # Verify webhook signature
        if not self._verify_webhook_signature(payload, headers, webhook_secret):
            raise ValueError("Invalid webhook signature")
        
        # Process webhook payload based on integration type
        if integration_slug == 'slack':
            return self._handle_slack_webhook(payload)
        elif integration_slug == 'github':
            return self._handle_github_webhook(payload)
        elif integration_slug == 'zapier':
            return self._handle_zapier_webhook(payload)
        else:
            # Generic webhook handling
            return {'status': 'received', 'payload': payload}
    
    def _encrypt_credentials(self, credentials: Dict[str, Any]) -> Dict[str, Any]:
        """Encrypt user credentials (simplified implementation)"""
        # In production, use proper encryption like AWS KMS or similar
        return credentials
    
    def _decrypt_credentials(self, encrypted_credentials: Dict[str, Any]) -> Dict[str, Any]:
        """Decrypt user credentials (simplified implementation)"""
        # In production, use proper decryption
        return encrypted_credentials
    
    def _generate_webhook_secret(self) -> str:
        """Generate a secure webhook secret"""
        import secrets
        return secrets.token_urlsafe(32)
    
    def _verify_webhook_signature(self, payload: Dict[str, Any], headers: Dict[str, str], secret: str) -> bool:
        """Verify webhook signature"""
        # Implementation depends on the specific integration
        # This is a simplified example
        signature = headers.get('X-Signature') or headers.get('X-Hub-Signature-256')
        if not signature:
            return False
        
        expected_signature = hmac.new(
            secret.encode(),
            json.dumps(payload).encode(),
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(signature, f"sha256={expected_signature}")
    
    def _test_integration(self, user_integration: UserIntegration, db: Session):
        """Test the integration connection"""
        try:
            # Perform a simple test request
            if user_integration.integration.slug == 'salesforce':
                self.execute_integration_request(user_integration, '/services/data/', 'GET')
            elif user_integration.integration.slug == 'slack':
                self.execute_integration_request(user_integration, '/auth.test', 'POST')
            # Add more test cases as needed
            
            user_integration.sync_status = "success"
        except Exception as e:
            user_integration.sync_status = "error"
            user_integration.error_message = str(e)
        
        db.commit()
    
    def _handle_slack_webhook(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle Slack webhook"""
        event_type = payload.get('type')
        if event_type == 'url_verification':
            return {'challenge': payload.get('challenge')}
        
        # Process other Slack events
        return {'status': 'processed'}
    
    def _handle_github_webhook(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle GitHub webhook"""
        event_type = payload.get('action')
        # Process GitHub events (issues, pull requests, etc.)
        return {'status': 'processed', 'event': event_type}
    
    def _handle_zapier_webhook(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle Zapier webhook"""
        # Process Zapier webhook data
        return {'status': 'processed', 'data_received': len(payload)}

# Global API marketplace manager instance
api_marketplace_manager = APIMarketplaceManager()
