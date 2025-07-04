from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, JSON, Float, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import enum

Base = declarative_base()

class UserRole(enum.Enum):
    CLIENT = "client"
    CONSULTANT = "consultant"
    ADMIN = "admin"

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
    company = Column(String)
    role = Column(Enum(UserRole), default=UserRole.CLIENT)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Profile information
    bio = Column(Text)
    skills = Column(JSON)  # List of skills for consultants
    hourly_rate = Column(Float)  # For consultants
    availability = Column(JSON)  # Availability schedule
    
    # Relationships
    projects = relationship("Project", back_populates="owner")
    consultant_projects = relationship("ConsultantProject", back_populates="consultant")
    ai_models = relationship("AIModel", back_populates="creator")
    reviews_given = relationship("Review", foreign_keys="Review.reviewer_id", back_populates="reviewer")
    reviews_received = relationship("Review", foreign_keys="Review.reviewee_id", back_populates="reviewee")

class Project(Base):
    __tablename__ = "projects"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    industry = Column(String)
    objectives = Column(Text)
    status = Column(String, default="active")
    budget = Column(Float)
    deadline = Column(DateTime)
    owner_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    owner = relationship("User", back_populates="projects")
    workflows = relationship("Workflow", back_populates="project")
    consultant_projects = relationship("ConsultantProject", back_populates="project")
    collaboration_sessions = relationship("CollaborationSession", back_populates="project")

class Workflow(Base):
    __tablename__ = "workflows"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    project_id = Column(Integer, ForeignKey("projects.id"))
    status = Column(String, default="draft")
    nodes = Column(JSON)  # Workflow nodes configuration
    edges = Column(JSON)  # Workflow edges configuration
    template_category = Column(String)  # Industry template category
    is_template = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    project = relationship("Project", back_populates="workflows")
    executions = relationship("WorkflowExecution", back_populates="workflow")

class WorkflowExecution(Base):
    __tablename__ = "workflow_executions"
    
    id = Column(Integer, primary_key=True, index=True)
    workflow_id = Column(Integer, ForeignKey("workflows.id"))
    status = Column(String, default="pending")  # pending, running, completed, failed
    input_data = Column(JSON)
    output_data = Column(JSON)
    error_message = Column(Text)
    execution_time = Column(Float)  # Execution time in seconds
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime)
    
    # Relationships
    workflow = relationship("Workflow", back_populates="executions")

class AIModel(Base):
    __tablename__ = "ai_models"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    model_type = Column(String, nullable=False)  # text, image, audio, etc.
    provider = Column(String, nullable=False)  # openai, huggingface, custom, etc.
    version = Column(String, default="1.0.0")
    api_endpoint = Column(String)
    pricing_model = Column(String)  # per_request, per_token, subscription
    price_per_unit = Column(Float)
    creator_id = Column(Integer, ForeignKey("users.id"))
    is_active = Column(Boolean, default=True)
    is_featured = Column(Boolean, default=False)
    category = Column(String)  # nlp, computer_vision, audio, etc.
    tags = Column(JSON)  # List of tags
    config_schema = Column(JSON)  # Configuration schema for the model
    sample_input = Column(JSON)  # Sample input for testing
    sample_output = Column(JSON)  # Sample output for testing
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Performance metrics
    total_requests = Column(Integer, default=0)
    average_response_time = Column(Float, default=0.0)
    success_rate = Column(Float, default=100.0)
    
    # Relationships
    creator = relationship("User", back_populates="ai_models")
    reviews = relationship("ModelReview", back_populates="model")
    usage_analytics = relationship("ModelUsageAnalytics", back_populates="model")

class ModelReview(Base):
    __tablename__ = "model_reviews"
    
    id = Column(Integer, primary_key=True, index=True)
    model_id = Column(Integer, ForeignKey("ai_models.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    rating = Column(Integer, nullable=False)  # 1-5 stars
    review_text = Column(Text)
    use_case = Column(String)  # What they used it for
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    model = relationship("AIModel", back_populates="reviews")
    user = relationship("User")

class ModelUsageAnalytics(Base):
    __tablename__ = "model_usage_analytics"
    
    id = Column(Integer, primary_key=True, index=True)
    model_id = Column(Integer, ForeignKey("ai_models.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    requests_count = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)
    total_cost = Column(Float, default=0.0)
    date = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    model = relationship("AIModel", back_populates="usage_analytics")
    user = relationship("User")

class ConsultantProject(Base):
    __tablename__ = "consultant_projects"
    
    id = Column(Integer, primary_key=True, index=True)
    consultant_id = Column(Integer, ForeignKey("users.id"))
    project_id = Column(Integer, ForeignKey("projects.id"))
    role = Column(String)  # lead, specialist, reviewer
    hourly_rate = Column(Float)
    hours_allocated = Column(Float)
    hours_worked = Column(Float, default=0.0)
    status = Column(String, default="active")  # active, completed, paused
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime)
    
    # Relationships
    consultant = relationship("User", back_populates="consultant_projects")
    project = relationship("Project", back_populates="consultant_projects")

class Review(Base):
    __tablename__ = "reviews"
    
    id = Column(Integer, primary_key=True, index=True)
    reviewer_id = Column(Integer, ForeignKey("users.id"))
    reviewee_id = Column(Integer, ForeignKey("users.id"))
    project_id = Column(Integer, ForeignKey("projects.id"))
    rating = Column(Integer, nullable=False)  # 1-5 stars
    review_text = Column(Text)
    review_type = Column(String)  # consultant_review, client_review
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    reviewer = relationship("User", foreign_keys=[reviewer_id], back_populates="reviews_given")
    reviewee = relationship("User", foreign_keys=[reviewee_id], back_populates="reviews_received")
    project = relationship("Project")

class CollaborationSession(Base):
    __tablename__ = "collaboration_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"))
    session_id = Column(String, unique=True, nullable=False)
    active_users = Column(JSON)  # List of currently active user IDs
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_activity = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    project = relationship("Project", back_populates="collaboration_sessions")

class Notification(Base):
    __tablename__ = "notifications"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    title = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    type = Column(String)  # info, warning, error, success
    is_read = Column(Boolean, default=False)
    action_url = Column(String)  # URL to navigate to when clicked
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User")

class Analytics(Base):
    __tablename__ = "analytics"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    event_type = Column(String, nullable=False)  # page_view, workflow_execution, etc.
    event_data = Column(JSON)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    session_id = Column(String)
    ip_address = Column(String)
    user_agent = Column(String)
    
    # Relationships
    user = relationship("User")
