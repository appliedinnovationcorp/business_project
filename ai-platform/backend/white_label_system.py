import os
import json
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from sqlalchemy import Column, Integer, String, Text, Boolean, JSON, DateTime, ForeignKey
from sqlalchemy.orm import Session, relationship
from datetime import datetime

from models import Base, User

@dataclass
class BrandingConfig:
    """Branding configuration for white-label clients"""
    primary_color: str = "#2563eb"
    secondary_color: str = "#1e40af"
    accent_color: str = "#3b82f6"
    background_color: str = "#ffffff"
    text_color: str = "#1f2937"
    logo_url: Optional[str] = None
    favicon_url: Optional[str] = None
    company_name: str = "AI Platform"
    tagline: Optional[str] = None
    font_family: str = "Inter, sans-serif"
    border_radius: str = "8px"
    custom_css: Optional[str] = None

@dataclass
class EmailTemplateConfig:
    """Email template configuration"""
    header_color: str = "#2563eb"
    footer_text: str = "Powered by AI Platform"
    support_email: str = "support@aiplatform.com"
    company_address: Optional[str] = None
    social_links: Dict[str, str] = None
    custom_header_html: Optional[str] = None
    custom_footer_html: Optional[str] = None

@dataclass
class DomainConfig:
    """Domain configuration for white-label deployment"""
    primary_domain: str
    api_subdomain: str = "api"
    cdn_subdomain: str = "cdn"
    ssl_enabled: bool = True
    custom_certificate: Optional[str] = None
    redirect_domains: List[str] = None

class WhiteLabelClient(Base):
    __tablename__ = "white_label_clients"
    
    id = Column(Integer, primary_key=True, index=True)
    client_name = Column(String, nullable=False)
    client_slug = Column(String, unique=True, nullable=False)  # URL-safe identifier
    domain_config = Column(JSON, nullable=False)
    branding_config = Column(JSON, nullable=False)
    email_config = Column(JSON, nullable=False)
    feature_flags = Column(JSON, default={})
    custom_integrations = Column(JSON, default={})
    subscription_tier = Column(String, default="enterprise")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    users = relationship("WhiteLabelUser", back_populates="client")
    custom_workflows = relationship("CustomWorkflowTemplate", back_populates="client")

class WhiteLabelUser(Base):
    __tablename__ = "white_label_users"
    
    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("white_label_clients.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    role_override = Column(String, nullable=True)  # Override default role for this client
    custom_permissions = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    client = relationship("WhiteLabelClient", back_populates="users")
    user = relationship("User")

class CustomWorkflowTemplate(Base):
    __tablename__ = "custom_workflow_templates"
    
    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("white_label_clients.id"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text)
    category = Column(String, nullable=False)
    template_data = Column(JSON, nullable=False)  # Workflow nodes and edges
    is_public = Column(Boolean, default=False)  # Available to all users of this client
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    client = relationship("WhiteLabelClient", back_populates="custom_workflows")
    creator = relationship("User")

class WhiteLabelManager:
    """Manages white-label client configurations and deployments"""
    
    def __init__(self):
        self.default_branding = BrandingConfig()
        self.default_email_config = EmailTemplateConfig()
    
    def create_white_label_client(self, db: Session, client_data: Dict[str, Any]) -> WhiteLabelClient:
        """Create a new white-label client"""
        
        # Generate client slug from name
        client_slug = self._generate_slug(client_data['client_name'])
        
        # Merge custom branding with defaults
        branding_config = asdict(self.default_branding)
        if 'branding_config' in client_data:
            branding_config.update(client_data['branding_config'])
        
        # Merge custom email config with defaults
        email_config = asdict(self.default_email_config)
        if 'email_config' in client_data:
            email_config.update(client_data['email_config'])
        
        # Create domain configuration
        domain_config = client_data.get('domain_config', {
            'primary_domain': f"{client_slug}.aiplatform.com",
            'api_subdomain': 'api',
            'cdn_subdomain': 'cdn',
            'ssl_enabled': True
        })
        
        client = WhiteLabelClient(
            client_name=client_data['client_name'],
            client_slug=client_slug,
            domain_config=domain_config,
            branding_config=branding_config,
            email_config=email_config,
            feature_flags=client_data.get('feature_flags', {}),
            custom_integrations=client_data.get('custom_integrations', {}),
            subscription_tier=client_data.get('subscription_tier', 'enterprise')
        )
        
        db.add(client)
        db.commit()
        db.refresh(client)
        
        # Generate deployment configuration
        self._generate_deployment_config(client)
        
        return client
    
    def update_client_branding(self, db: Session, client_id: int, branding_updates: Dict[str, Any]) -> WhiteLabelClient:
        """Update client branding configuration"""
        client = db.query(WhiteLabelClient).filter(WhiteLabelClient.id == client_id).first()
        if not client:
            raise ValueError(f"Client with ID {client_id} not found")
        
        # Update branding configuration
        current_branding = client.branding_config
        current_branding.update(branding_updates)
        client.branding_config = current_branding
        client.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(client)
        
        # Regenerate CSS and deployment files
        self._generate_custom_css(client)
        
        return client
    
    def get_client_by_domain(self, db: Session, domain: str) -> Optional[WhiteLabelClient]:
        """Get white-label client by domain"""
        clients = db.query(WhiteLabelClient).filter(WhiteLabelClient.is_active == True).all()
        
        for client in clients:
            domain_config = client.domain_config
            if (domain == domain_config.get('primary_domain') or 
                domain in domain_config.get('redirect_domains', [])):
                return client
        
        return None
    
    def get_client_config(self, db: Session, client_id: int) -> Dict[str, Any]:
        """Get complete client configuration for frontend"""
        client = db.query(WhiteLabelClient).filter(WhiteLabelClient.id == client_id).first()
        if not client:
            raise ValueError(f"Client with ID {client_id} not found")
        
        return {
            'client_info': {
                'id': client.id,
                'name': client.client_name,
                'slug': client.client_slug,
                'subscription_tier': client.subscription_tier
            },
            'branding': client.branding_config,
            'domain': client.domain_config,
            'email_config': client.email_config,
            'feature_flags': client.feature_flags,
            'custom_integrations': client.custom_integrations,
            'custom_css_url': f"/api/white-label/{client.client_slug}/styles.css"
        }
    
    def generate_custom_css(self, client: WhiteLabelClient) -> str:
        """Generate custom CSS for white-label client"""
        branding = client.branding_config
        
        css_template = f"""
        :root {{
            --primary-color: {branding.get('primary_color', '#2563eb')};
            --secondary-color: {branding.get('secondary_color', '#1e40af')};
            --accent-color: {branding.get('accent_color', '#3b82f6')};
            --background-color: {branding.get('background_color', '#ffffff')};
            --text-color: {branding.get('text_color', '#1f2937')};
            --border-radius: {branding.get('border_radius', '8px')};
            --font-family: {branding.get('font_family', 'Inter, sans-serif')};
        }}
        
        body {{
            font-family: var(--font-family);
            color: var(--text-color);
            background-color: var(--background-color);
        }}
        
        .btn-primary {{
            background-color: var(--primary-color);
            border-color: var(--primary-color);
            border-radius: var(--border-radius);
        }}
        
        .btn-primary:hover {{
            background-color: var(--secondary-color);
            border-color: var(--secondary-color);
        }}
        
        .navbar-brand {{
            color: var(--primary-color) !important;
        }}
        
        .card {{
            border-radius: var(--border-radius);
        }}
        
        .form-control {{
            border-radius: var(--border-radius);
        }}
        
        .alert-primary {{
            background-color: var(--accent-color);
            border-color: var(--primary-color);
        }}
        
        /* Custom CSS from client */
        {branding.get('custom_css', '')}
        """
        
        return css_template
    
    def _generate_slug(self, client_name: str) -> str:
        """Generate URL-safe slug from client name"""
        import re
        slug = re.sub(r'[^a-zA-Z0-9\s-]', '', client_name.lower())
        slug = re.sub(r'\s+', '-', slug)
        return slug.strip('-')
    
    def _generate_deployment_config(self, client: WhiteLabelClient):
        """Generate deployment configuration files"""
        config = {
            'client_id': client.id,
            'client_slug': client.client_slug,
            'domain_config': client.domain_config,
            'environment_variables': {
                'REACT_APP_CLIENT_ID': str(client.id),
                'REACT_APP_CLIENT_SLUG': client.client_slug,
                'REACT_APP_API_URL': f"https://{client.domain_config['api_subdomain']}.{client.domain_config['primary_domain']}",
                'REACT_APP_CDN_URL': f"https://{client.domain_config['cdn_subdomain']}.{client.domain_config['primary_domain']}",
            },
            'nginx_config': self._generate_nginx_config(client),
            'docker_config': self._generate_docker_config(client)
        }
        
        # Save configuration to file system or database
        config_path = f"/tmp/white-label-configs/{client.client_slug}"
        os.makedirs(config_path, exist_ok=True)
        
        with open(f"{config_path}/deployment-config.json", 'w') as f:
            json.dump(config, f, indent=2)
    
    def _generate_nginx_config(self, client: WhiteLabelClient) -> str:
        """Generate Nginx configuration for white-label client"""
        domain_config = client.domain_config
        
        nginx_config = f"""
        server {{
            listen 80;
            listen 443 ssl http2;
            server_name {domain_config['primary_domain']};
            
            # SSL Configuration
            ssl_certificate /etc/ssl/certs/{client.client_slug}.crt;
            ssl_certificate_key /etc/ssl/private/{client.client_slug}.key;
            
            # Security headers
            add_header X-Frame-Options DENY;
            add_header X-Content-Type-Options nosniff;
            add_header X-XSS-Protection "1; mode=block";
            add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
            
            # Custom branding headers
            add_header X-Client-ID "{client.id}";
            add_header X-Client-Slug "{client.client_slug}";
            
            # Frontend
            location / {{
                root /var/www/{client.client_slug}/build;
                try_files $uri $uri/ /index.html;
                
                # Cache static assets
                location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {{
                    expires 1y;
                    add_header Cache-Control "public, immutable";
                }}
            }}
            
            # API proxy
            location /api/ {{
                proxy_pass http://backend-{client.client_slug}:8000;
                proxy_set_header Host $host;
                proxy_set_header X-Real-IP $remote_addr;
                proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
                proxy_set_header X-Forwarded-Proto $scheme;
                proxy_set_header X-Client-ID "{client.id}";
            }}
            
            # Custom CSS endpoint
            location /api/white-label/{client.client_slug}/styles.css {{
                proxy_pass http://backend-{client.client_slug}:8000/white-label/styles.css;
                add_header Content-Type text/css;
                add_header Cache-Control "public, max-age=3600";
            }}
        }}
        """
        
        return nginx_config
    
    def _generate_docker_config(self, client: WhiteLabelClient) -> Dict[str, str]:
        """Generate Docker configuration for white-label client"""
        
        dockerfile_frontend = f"""
        FROM node:18-alpine AS builder
        
        WORKDIR /app
        COPY package*.json ./
        RUN npm ci --only=production
        
        # Copy source and build with client-specific config
        COPY . .
        ENV REACT_APP_CLIENT_ID={client.id}
        ENV REACT_APP_CLIENT_SLUG={client.client_slug}
        ENV REACT_APP_API_URL=https://{client.domain_config['api_subdomain']}.{client.domain_config['primary_domain']}
        
        RUN npm run build
        
        FROM nginx:alpine
        COPY --from=builder /app/build /var/www/{client.client_slug}/build
        COPY nginx.conf /etc/nginx/conf.d/default.conf
        
        EXPOSE 80 443
        CMD ["nginx", "-g", "daemon off;"]
        """
        
        dockerfile_backend = f"""
        FROM python:3.9-slim
        
        WORKDIR /app
        COPY requirements.txt .
        RUN pip install --no-cache-dir -r requirements.txt
        
        COPY . .
        
        # Client-specific environment variables
        ENV CLIENT_ID={client.id}
        ENV CLIENT_SLUG={client.client_slug}
        ENV WHITE_LABEL_MODE=true
        
        EXPOSE 8000
        CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
        """
        
        docker_compose = f"""
        version: '3.8'
        
        services:
          frontend-{client.client_slug}:
            build:
              context: ./frontend
              dockerfile: Dockerfile.{client.client_slug}
            ports:
              - "80:80"
              - "443:443"
            volumes:
              - ./ssl:/etc/ssl
            depends_on:
              - backend-{client.client_slug}
        
          backend-{client.client_slug}:
            build:
              context: ./backend
              dockerfile: Dockerfile.{client.client_slug}
            environment:
              - DATABASE_URL=${{DATABASE_URL}}
              - CLIENT_ID={client.id}
              - CLIENT_SLUG={client.client_slug}
            depends_on:
              - database
        
          database:
            image: postgres:13
            environment:
              - POSTGRES_DB=aiplatform_{client.client_slug}
              - POSTGRES_USER=${{DB_USER}}
              - POSTGRES_PASSWORD=${{DB_PASSWORD}}
            volumes:
              - postgres_data_{client.client_slug}:/var/lib/postgresql/data
        
        volumes:
          postgres_data_{client.client_slug}:
        """
        
        return {
            'dockerfile_frontend': dockerfile_frontend,
            'dockerfile_backend': dockerfile_backend,
            'docker_compose': docker_compose
        }
    
    def create_custom_workflow_template(self, db: Session, client_id: int, template_data: Dict[str, Any]) -> CustomWorkflowTemplate:
        """Create a custom workflow template for a white-label client"""
        template = CustomWorkflowTemplate(
            client_id=client_id,
            name=template_data['name'],
            description=template_data.get('description', ''),
            category=template_data['category'],
            template_data=template_data['template_data'],
            is_public=template_data.get('is_public', False),
            created_by=template_data.get('created_by')
        )
        
        db.add(template)
        db.commit()
        db.refresh(template)
        
        return template
    
    def get_client_workflow_templates(self, db: Session, client_id: int) -> List[CustomWorkflowTemplate]:
        """Get custom workflow templates for a client"""
        return db.query(CustomWorkflowTemplate).filter(
            CustomWorkflowTemplate.client_id == client_id,
            CustomWorkflowTemplate.is_public == True
        ).all()
    
    def generate_mobile_app_config(self, client: WhiteLabelClient) -> Dict[str, Any]:
        """Generate mobile app configuration for white-label client"""
        branding = client.branding_config
        
        return {
            'app_name': branding.get('company_name', 'AI Platform'),
            'bundle_id': f"com.aiplatform.{client.client_slug}",
            'colors': {
                'primary': branding.get('primary_color', '#2563eb'),
                'secondary': branding.get('secondary_color', '#1e40af'),
                'accent': branding.get('accent_color', '#3b82f6'),
                'background': branding.get('background_color', '#ffffff'),
                'text': branding.get('text_color', '#1f2937')
            },
            'assets': {
                'logo': branding.get('logo_url'),
                'icon': branding.get('favicon_url'),
                'splash_screen': branding.get('splash_screen_url')
            },
            'api_config': {
                'base_url': f"https://{client.domain_config['api_subdomain']}.{client.domain_config['primary_domain']}",
                'client_id': str(client.id),
                'client_slug': client.client_slug
            },
            'feature_flags': client.feature_flags
        }

# Global white-label manager instance
white_label_manager = WhiteLabelManager()
