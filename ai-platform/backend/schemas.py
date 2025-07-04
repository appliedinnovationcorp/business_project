from pydantic import BaseModel, EmailStr
from typing import Optional, Dict, Any, List
from datetime import datetime

# User schemas
class UserBase(BaseModel):
    email: EmailStr
    full_name: str
    company: Optional[str] = None

class UserCreate(UserBase):
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(UserBase):
    id: int
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

# Project schemas
class ProjectBase(BaseModel):
    name: str
    description: str
    industry: Optional[str] = None
    objectives: Optional[str] = None

class ProjectCreate(ProjectBase):
    pass

class ProjectResponse(ProjectBase):
    id: int
    status: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# Workflow schemas
class WorkflowBase(BaseModel):
    name: str
    description: str
    nodes: Optional[List[Any]] = []
    edges: Optional[List[Any]] = []

class WorkflowCreate(WorkflowBase):
    pass

class WorkflowResponse(WorkflowBase):
    id: int
    status: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# Workflow execution schemas
class WorkflowExecutionResponse(BaseModel):
    id: int
    workflow_id: int
    status: str
    input_data: Optional[Dict[str, Any]] = None
    output_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    started_at: datetime
    completed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

# AI Model schemas
class AIModelBase(BaseModel):
    name: str
    description: Optional[str] = None
    model_type: str
    provider: str
    config: Optional[Dict[str, Any]] = None

class AIModelCreate(AIModelBase):
    pass

class AIModelResponse(AIModelBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True
