from fastapi import FastAPI, HTTPException, Depends, status, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional, Dict, Any
import os
import json
from datetime import datetime
from dotenv import load_dotenv

from database import get_db, engine
from models import Base, User, Project, Workflow
from schemas import UserCreate, UserResponse, ProjectCreate, ProjectResponse, WorkflowCreate, WorkflowResponse, UserLogin
from auth import get_password_hash, verify_password, create_access_token, verify_token
from aws_services import AWSServices

# Load environment variables
load_dotenv()

# Create database tables
Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI(
    title="AI Platform API",
    description="AI Consulting Platform Backend API",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],  # Frontend URLs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize AWS services
aws_services = AWSServices()

# Security
security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    """Get current authenticated user"""
    try:
        payload = verify_token(credentials.credentials)
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        user = db.query(User).filter(User.id == user_id).first()
        if user is None:
            raise HTTPException(status_code=401, detail="User not found")
        return user
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid token")

# Health check endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "AI Platform API is running", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.utcnow()}

# Authentication endpoints
@app.post("/auth/register", response_model=UserResponse)
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """Register a new user"""
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create new user
    hashed_password = get_password_hash(user_data.password)
    user = User(
        email=user_data.email,
        hashed_password=hashed_password,
        full_name=user_data.full_name,
        company=user_data.company
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return UserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        company=user.company,
        is_active=user.is_active,
        created_at=user.created_at
    )

@app.post("/auth/login")
async def login(user_data: UserLogin, db: Session = Depends(get_db)):
    """Login user"""
    user = db.query(User).filter(User.email == user_data.email).first()
    if not user or not verify_password(user_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    if not user.is_active:
        raise HTTPException(status_code=401, detail="Account is inactive")
    
    access_token = create_access_token(data={"sub": str(user.id)})
    return {"access_token": access_token, "token_type": "bearer"}

# Dashboard endpoints
@app.get("/dashboard/stats")
async def get_dashboard_stats(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get dashboard statistics"""
    total_projects = db.query(Project).filter(Project.owner_id == current_user.id).count()
    active_workflows = db.query(Workflow).join(Project).filter(
        Project.owner_id == current_user.id,
        Workflow.status == "active"
    ).count()
    
    return {
        "total_projects": total_projects,
        "active_workflows": active_workflows,
        "completed_tasks": 0,  # TODO: Implement task tracking
        "ai_services_used": 3  # Static for now
    }

# Project endpoints
@app.get("/projects", response_model=List[ProjectResponse])
async def get_projects(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get user's projects"""
    projects = db.query(Project).filter(Project.owner_id == current_user.id).all()
    return [ProjectResponse(
        id=p.id,
        name=p.name,
        description=p.description,
        industry=p.industry,
        objectives=p.objectives,
        status=p.status,
        created_at=p.created_at,
        updated_at=p.updated_at
    ) for p in projects]

@app.post("/projects", response_model=ProjectResponse)
async def create_project(project_data: ProjectCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Create a new project"""
    project = Project(
        name=project_data.name,
        description=project_data.description,
        industry=project_data.industry,
        objectives=project_data.objectives,
        owner_id=current_user.id
    )
    
    db.add(project)
    db.commit()
    db.refresh(project)
    
    return ProjectResponse(
        id=project.id,
        name=project.name,
        description=project.description,
        industry=project.industry,
        objectives=project.objectives,
        status=project.status,
        created_at=project.created_at,
        updated_at=project.updated_at
    )

@app.get("/projects/{project_id}", response_model=ProjectResponse)
async def get_project(project_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get a specific project"""
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.owner_id == current_user.id
    ).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    return ProjectResponse(
        id=project.id,
        name=project.name,
        description=project.description,
        industry=project.industry,
        objectives=project.objectives,
        status=project.status,
        created_at=project.created_at,
        updated_at=project.updated_at
    )

# Workflow endpoints
@app.get("/projects/{project_id}/workflows", response_model=List[WorkflowResponse])
async def get_workflows(project_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get workflows for a project"""
    # Verify project ownership
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.owner_id == current_user.id
    ).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    workflows = db.query(Workflow).filter(Workflow.project_id == project_id).all()
    return [WorkflowResponse(
        id=w.id,
        name=w.name,
        description=w.description,
        status=w.status,
        nodes=json.loads(w.nodes) if w.nodes else [],
        edges=json.loads(w.edges) if w.edges else [],
        created_at=w.created_at,
        updated_at=w.updated_at
    ) for w in workflows]

@app.post("/projects/{project_id}/workflows", response_model=WorkflowResponse)
async def create_workflow(
    project_id: int, 
    workflow_data: WorkflowCreate, 
    current_user: User = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    """Create a new workflow"""
    # Verify project ownership
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.owner_id == current_user.id
    ).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    workflow = Workflow(
        name=workflow_data.name,
        description=workflow_data.description,
        project_id=project_id,
        nodes=json.dumps(workflow_data.nodes) if workflow_data.nodes else "[]",
        edges=json.dumps(workflow_data.edges) if workflow_data.edges else "[]"
    )
    
    db.add(workflow)
    db.commit()
    db.refresh(workflow)
    
    return WorkflowResponse(
        id=workflow.id,
        name=workflow.name,
        description=workflow.description,
        status=workflow.status,
        nodes=json.loads(workflow.nodes) if workflow.nodes else [],
        edges=json.loads(workflow.edges) if workflow.edges else [],
        created_at=workflow.created_at,
        updated_at=workflow.updated_at
    )

@app.put("/workflows/{workflow_id}", response_model=WorkflowResponse)
async def update_workflow(
    workflow_id: int,
    workflow_data: WorkflowCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a workflow"""
    workflow = db.query(Workflow).join(Project).filter(
        Workflow.id == workflow_id,
        Project.owner_id == current_user.id
    ).first()
    
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    workflow.name = workflow_data.name
    workflow.description = workflow_data.description
    workflow.nodes = json.dumps(workflow_data.nodes) if workflow_data.nodes else "[]"
    workflow.edges = json.dumps(workflow_data.edges) if workflow_data.edges else "[]"
    workflow.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(workflow)
    
    return WorkflowResponse(
        id=workflow.id,
        name=workflow.name,
        description=workflow.description,
        status=workflow.status,
        nodes=json.loads(workflow.nodes) if workflow.nodes else [],
        edges=json.loads(workflow.edges) if workflow.edges else [],
        created_at=workflow.created_at,
        updated_at=workflow.updated_at
    )

@app.post("/workflows/{workflow_id}/execute")
async def execute_workflow(
    workflow_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Execute a workflow"""
    workflow = db.query(Workflow).join(Project).filter(
        Workflow.id == workflow_id,
        Project.owner_id == current_user.id
    ).first()
    
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    # Update workflow status
    workflow.status = "running"
    workflow.updated_at = datetime.utcnow()
    db.commit()
    
    # TODO: Implement actual workflow execution logic
    # For now, just return success
    return {"message": "Workflow execution started", "workflow_id": workflow_id}

# AI Services endpoints
@app.post("/ai/textract/analyze")
async def analyze_document(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """Analyze document with AWS Textract"""
    try:
        content = await file.read()
        result = aws_services.analyze_document(content)
        return {"result": result, "filename": file.filename}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Document analysis failed: {str(e)}")

@app.post("/ai/comprehend/sentiment")
async def analyze_sentiment(
    text: Dict[str, str],
    current_user: User = Depends(get_current_user)
):
    """Analyze text sentiment with AWS Comprehend"""
    try:
        result = aws_services.analyze_sentiment(text["text"])
        return {"result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sentiment analysis failed: {str(e)}")

@app.post("/ai/rekognition/analyze")
async def analyze_image(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """Analyze image with AWS Rekognition"""
    try:
        content = await file.read()
        result = aws_services.analyze_image(content)
        return {"result": result, "filename": file.filename}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Image analysis failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
