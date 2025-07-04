import os
import jwt
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from urllib.parse import urlparse, parse_qs
import requests
import base64
import hashlib
import secrets
from cryptography.x509 import load_pem_x509_certificate
from cryptography.hazmat.backends import default_backend
import xmlsec

from fastapi import HTTPException, Request
from sqlalchemy.orm import Session
from models import User, UserRole
from auth import create_access_token

class SSOProvider:
    """Base class for SSO providers"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.provider_name = config.get('provider_name', 'unknown')
    
    async def authenticate(self, request: Request) -> Dict[str, Any]:
        """Authenticate user via SSO provider"""
        raise NotImplementedError
    
    async def get_user_info(self, token: str) -> Dict[str, Any]:
        """Get user information from SSO provider"""
        raise NotImplementedError

class SAMLProvider(SSOProvider):
    """SAML 2.0 SSO Provider"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.entity_id = config['entity_id']
        self.sso_url = config['sso_url']
        self.x509_cert = config['x509_cert']
        self.private_key = config.get('private_key')
        
    def generate_saml_request(self, relay_state: Optional[str] = None) -> str:
        """Generate SAML authentication request"""
        request_id = f"_{secrets.token_hex(16)}"
        issue_instant = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
        
        saml_request = f"""
        <samlp:AuthnRequest
            xmlns:samlp="urn:oasis:names:tc:SAML:2.0:protocol"
            xmlns:saml="urn:oasis:names:tc:SAML:2.0:assertion"
            ID="{request_id}"
            Version="2.0"
            IssueInstant="{issue_instant}"
            Destination="{self.sso_url}"
            ProtocolBinding="urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST"
            AssertionConsumerServiceURL="{self.config['acs_url']}">
            <saml:Issuer>{self.entity_id}</saml:Issuer>
            <samlp:NameIDPolicy Format="urn:oasis:names:tc:SAML:2.0:nameid-format:emailAddress" AllowCreate="true"/>
        </samlp:AuthnRequest>
        """
        
        # Encode and compress the request
        encoded_request = base64.b64encode(saml_request.encode()).decode()
        
        return encoded_request
    
    async def process_saml_response(self, saml_response: str) -> Dict[str, Any]:
        """Process SAML response and extract user information"""
        try:
            # Decode the SAML response
            decoded_response = base64.b64decode(saml_response)
            
            # Parse XML
            root = ET.fromstring(decoded_response)
            
            # Verify signature (simplified - use proper SAML library in production)
            if not self._verify_signature(root):
                raise HTTPException(status_code=401, detail="Invalid SAML signature")
            
            # Extract user attributes
            user_info = self._extract_user_attributes(root)
            
            return user_info
            
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid SAML response: {str(e)}")
    
    def _verify_signature(self, xml_root) -> bool:
        """Verify SAML response signature"""
        # Simplified signature verification
        # In production, use proper SAML library like python3-saml
        return True
    
    def _extract_user_attributes(self, xml_root) -> Dict[str, Any]:
        """Extract user attributes from SAML assertion"""
        namespaces = {
            'saml': 'urn:oasis:names:tc:SAML:2.0:assertion',
            'samlp': 'urn:oasis:names:tc:SAML:2.0:protocol'
        }
        
        # Find assertion
        assertion = xml_root.find('.//saml:Assertion', namespaces)
        if assertion is None:
            raise ValueError("No assertion found in SAML response")
        
        # Extract NameID (usually email)
        name_id = assertion.find('.//saml:NameID', namespaces)
        email = name_id.text if name_id is not None else None
        
        # Extract attributes
        attributes = {}
        attr_statements = assertion.findall('.//saml:AttributeStatement/saml:Attribute', namespaces)
        
        for attr in attr_statements:
            attr_name = attr.get('Name')
            attr_values = [val.text for val in attr.findall('saml:AttributeValue', namespaces)]
            attributes[attr_name] = attr_values[0] if len(attr_values) == 1 else attr_values
        
        return {
            'email': email,
            'full_name': attributes.get('http://schemas.xmlsoap.org/ws/2005/05/identity/claims/name', ''),
            'first_name': attributes.get('http://schemas.xmlsoap.org/ws/2005/05/identity/claims/givenname', ''),
            'last_name': attributes.get('http://schemas.xmlsoap.org/ws/2005/05/identity/claims/surname', ''),
            'groups': attributes.get('http://schemas.microsoft.com/ws/2008/06/identity/claims/groups', []),
            'department': attributes.get('http://schemas.xmlsoap.org/ws/2005/05/identity/claims/department', ''),
            'company': attributes.get('http://schemas.xmlsoap.org/ws/2005/05/identity/claims/company', ''),
        }

class OAuthProvider(SSOProvider):
    """OAuth 2.0 / OpenID Connect Provider"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.client_id = config['client_id']
        self.client_secret = config['client_secret']
        self.authorization_url = config['authorization_url']
        self.token_url = config['token_url']
        self.userinfo_url = config['userinfo_url']
        self.redirect_uri = config['redirect_uri']
        self.scopes = config.get('scopes', ['openid', 'email', 'profile'])
    
    def get_authorization_url(self, state: str) -> str:
        """Generate OAuth authorization URL"""
        params = {
            'client_id': self.client_id,
            'response_type': 'code',
            'scope': ' '.join(self.scopes),
            'redirect_uri': self.redirect_uri,
            'state': state,
        }
        
        query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
        return f"{self.authorization_url}?{query_string}"
    
    async def exchange_code_for_token(self, code: str, state: str) -> Dict[str, Any]:
        """Exchange authorization code for access token"""
        data = {
            'grant_type': 'authorization_code',
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'code': code,
            'redirect_uri': self.redirect_uri,
        }
        
        response = requests.post(self.token_url, data=data)
        
        if response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to exchange code for token")
        
        return response.json()
    
    async def get_user_info(self, access_token: str) -> Dict[str, Any]:
        """Get user information using access token"""
        headers = {'Authorization': f'Bearer {access_token}'}
        response = requests.get(self.userinfo_url, headers=headers)
        
        if response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to get user info")
        
        user_data = response.json()
        
        return {
            'email': user_data.get('email'),
            'full_name': user_data.get('name', ''),
            'first_name': user_data.get('given_name', ''),
            'last_name': user_data.get('family_name', ''),
            'company': user_data.get('organization', ''),
            'groups': user_data.get('groups', []),
            'department': user_data.get('department', ''),
        }

class AzureADProvider(OAuthProvider):
    """Microsoft Azure Active Directory Provider"""
    
    def __init__(self, config: Dict[str, Any]):
        tenant_id = config['tenant_id']
        config.update({
            'authorization_url': f'https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/authorize',
            'token_url': f'https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token',
            'userinfo_url': 'https://graph.microsoft.com/v1.0/me',
            'scopes': ['openid', 'email', 'profile', 'User.Read'],
        })
        super().__init__(config)
    
    async def get_user_info(self, access_token: str) -> Dict[str, Any]:
        """Get user information from Microsoft Graph API"""
        headers = {'Authorization': f'Bearer {access_token}'}
        response = requests.get(self.userinfo_url, headers=headers)
        
        if response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to get user info from Azure AD")
        
        user_data = response.json()
        
        return {
            'email': user_data.get('mail') or user_data.get('userPrincipalName'),
            'full_name': user_data.get('displayName', ''),
            'first_name': user_data.get('givenName', ''),
            'last_name': user_data.get('surname', ''),
            'company': user_data.get('companyName', ''),
            'department': user_data.get('department', ''),
            'job_title': user_data.get('jobTitle', ''),
        }

class OktaProvider(OAuthProvider):
    """Okta SSO Provider"""
    
    def __init__(self, config: Dict[str, Any]):
        okta_domain = config['okta_domain']
        config.update({
            'authorization_url': f'https://{okta_domain}/oauth2/default/v1/authorize',
            'token_url': f'https://{okta_domain}/oauth2/default/v1/token',
            'userinfo_url': f'https://{okta_domain}/oauth2/default/v1/userinfo',
            'scopes': ['openid', 'email', 'profile', 'groups'],
        })
        super().__init__(config)

class GoogleWorkspaceProvider(OAuthProvider):
    """Google Workspace SSO Provider"""
    
    def __init__(self, config: Dict[str, Any]):
        config.update({
            'authorization_url': 'https://accounts.google.com/o/oauth2/v2/auth',
            'token_url': 'https://oauth2.googleapis.com/token',
            'userinfo_url': 'https://www.googleapis.com/oauth2/v2/userinfo',
            'scopes': ['openid', 'email', 'profile'],
        })
        super().__init__(config)

class SSOManager:
    """Centralized SSO management"""
    
    def __init__(self):
        self.providers: Dict[str, SSOProvider] = {}
        self._load_providers()
    
    def _load_providers(self):
        """Load SSO providers from configuration"""
        # Azure AD
        if os.getenv('AZURE_AD_ENABLED') == 'true':
            azure_config = {
                'provider_name': 'azure_ad',
                'client_id': os.getenv('AZURE_AD_CLIENT_ID'),
                'client_secret': os.getenv('AZURE_AD_CLIENT_SECRET'),
                'tenant_id': os.getenv('AZURE_AD_TENANT_ID'),
                'redirect_uri': os.getenv('AZURE_AD_REDIRECT_URI'),
            }
            self.providers['azure_ad'] = AzureADProvider(azure_config)
        
        # Okta
        if os.getenv('OKTA_ENABLED') == 'true':
            okta_config = {
                'provider_name': 'okta',
                'client_id': os.getenv('OKTA_CLIENT_ID'),
                'client_secret': os.getenv('OKTA_CLIENT_SECRET'),
                'okta_domain': os.getenv('OKTA_DOMAIN'),
                'redirect_uri': os.getenv('OKTA_REDIRECT_URI'),
            }
            self.providers['okta'] = OktaProvider(okta_config)
        
        # Google Workspace
        if os.getenv('GOOGLE_WORKSPACE_ENABLED') == 'true':
            google_config = {
                'provider_name': 'google_workspace',
                'client_id': os.getenv('GOOGLE_WORKSPACE_CLIENT_ID'),
                'client_secret': os.getenv('GOOGLE_WORKSPACE_CLIENT_SECRET'),
                'redirect_uri': os.getenv('GOOGLE_WORKSPACE_REDIRECT_URI'),
            }
            self.providers['google_workspace'] = GoogleWorkspaceProvider(google_config)
        
        # SAML Provider
        if os.getenv('SAML_ENABLED') == 'true':
            saml_config = {
                'provider_name': 'saml',
                'entity_id': os.getenv('SAML_ENTITY_ID'),
                'sso_url': os.getenv('SAML_SSO_URL'),
                'x509_cert': os.getenv('SAML_X509_CERT'),
                'acs_url': os.getenv('SAML_ACS_URL'),
            }
            self.providers['saml'] = SAMLProvider(saml_config)
    
    def get_provider(self, provider_name: str) -> Optional[SSOProvider]:
        """Get SSO provider by name"""
        return self.providers.get(provider_name)
    
    def list_providers(self) -> List[str]:
        """List available SSO providers"""
        return list(self.providers.keys())
    
    async def authenticate_user(self, provider_name: str, auth_data: Dict[str, Any], db: Session) -> Dict[str, Any]:
        """Authenticate user via SSO and create/update user record"""
        provider = self.get_provider(provider_name)
        if not provider:
            raise HTTPException(status_code=400, detail=f"Unknown SSO provider: {provider_name}")
        
        # Get user info from SSO provider
        if provider_name == 'saml':
            user_info = await provider.process_saml_response(auth_data['saml_response'])
        else:
            # OAuth flow
            token_data = await provider.exchange_code_for_token(
                auth_data['code'], 
                auth_data['state']
            )
            user_info = await provider.get_user_info(token_data['access_token'])
        
        # Create or update user
        user = self._create_or_update_user(user_info, provider_name, db)
        
        # Generate JWT token
        access_token = create_access_token(data={"sub": str(user.id)})
        
        return {
            'access_token': access_token,
            'token_type': 'bearer',
            'user': {
                'id': user.id,
                'email': user.email,
                'full_name': user.full_name,
                'role': user.role.value,
            }
        }
    
    def _create_or_update_user(self, user_info: Dict[str, Any], provider_name: str, db: Session) -> User:
        """Create or update user from SSO information"""
        email = user_info.get('email')
        if not email:
            raise HTTPException(status_code=400, detail="Email not provided by SSO provider")
        
        # Check if user exists
        user = db.query(User).filter(User.email == email).first()
        
        if user:
            # Update existing user
            user.full_name = user_info.get('full_name', user.full_name)
            user.company = user_info.get('company', user.company)
            user.updated_at = datetime.utcnow()
        else:
            # Create new user
            user = User(
                email=email,
                full_name=user_info.get('full_name', ''),
                company=user_info.get('company', ''),
                hashed_password='',  # No password for SSO users
                role=self._determine_user_role(user_info, provider_name),
                is_active=True,
            )
            db.add(user)
        
        db.commit()
        db.refresh(user)
        
        return user
    
    def _determine_user_role(self, user_info: Dict[str, Any], provider_name: str) -> UserRole:
        """Determine user role based on SSO attributes"""
        groups = user_info.get('groups', [])
        
        # Check for admin groups
        admin_groups = ['AI Platform Admins', 'Administrators', 'Admin']
        if any(group in admin_groups for group in groups):
            return UserRole.ADMIN
        
        # Check for consultant groups
        consultant_groups = ['AI Consultants', 'Consultants', 'Experts']
        if any(group in consultant_groups for group in groups):
            return UserRole.CONSULTANT
        
        # Default to client
        return UserRole.CLIENT

# Multi-Factor Authentication
class MFAManager:
    """Multi-Factor Authentication management"""
    
    @staticmethod
    def generate_totp_secret() -> str:
        """Generate TOTP secret for user"""
        return base64.b32encode(secrets.token_bytes(20)).decode()
    
    @staticmethod
    def verify_totp(secret: str, token: str) -> bool:
        """Verify TOTP token"""
        import pyotp
        totp = pyotp.TOTP(secret)
        return totp.verify(token, valid_window=1)
    
    @staticmethod
    def generate_backup_codes() -> List[str]:
        """Generate backup codes for MFA"""
        return [secrets.token_hex(4).upper() for _ in range(10)]

# Global SSO manager instance
sso_manager = SSOManager()
