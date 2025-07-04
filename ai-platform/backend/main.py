from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import List, Optional
import os
from dotenv import load_dotenv

from database import get_db, engine
from models import Base, User, Project, Workflow
from schemas import UserCreate, UserResponse, ProjectCreate, ProjectResponse, WorkflowCreate, WorkflowResponse
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
    allow_origins=["http://localhost:3000"],  # Frontend URL
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
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "AI Platform API is running", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    """Detailed health check"""
    try:
        # Test database connection
        db = next(get_db())
        db.execute("SELECT 1")
        db_status = "healthy"
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"
    
    try:
        # Test AWS connection
        aws_status = await aws_services.health_check()
    except Exception as e:
        aws_status = f"unhealthy: {str(e)}"
    
    return {
        "status": "healthy" if db_status == "healthy" and "healthy" in aws_status else "unhealthy",
        "database": db_status,
        "aws": aws_status,
        "version": "1.0.0"
    }

# Authentication endpoints
@app.post("/auth/register", response_model=UserResponse)
async def register(user: UserCreate, db: Session = Depends(get_db)):
    """Register a new user"""
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == user.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create new user
    hashed_password = get_password_hash(user.password)
    db_user = User(
        email=user.email,
        full_name=user.full_name,
        hashed_password=hashed_password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return UserResponse(
        id=db_user.id,
        email=db_user.email,
        full_name=db_user.full_name,
        is_active=db_user.is_active,
        created_at=db_user.created_at
    )

@app.post("/auth/login")
async def login(email: str, password: str, db: Session = Depends(get_db)):
    """Login user and return access token"""
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    if not user.is_active:
        raise HTTPException(status_code=401, detail="User account is disabled")
    
    access_token = create_access_token(data={"sub": str(user.id)})
    return {"access_token": access_token, "token_type": "bearer"}

# Project endpoints
@app.get("/projects", response_model=List[ProjectResponse])
async def get_projects(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get all projects for the current user"""
    projects = db.query(Project).filter(Project.user_id == current_user.id).all()
    return projects

@app.post("/projects", response_model=ProjectResponse)
async def create_project(project: ProjectCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Create a new project"""
    db_project = Project(
        name=project.name,
        description=project.description,
        user_id=current_user.id
    )
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return db_project

@app.get("/projects/{project_id}", response_model=ProjectResponse)
async def get_project(project_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get a specific project"""
    project = db.query(Project).filter(Project.id == project_id, Project.user_id == current_user.id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project

# Workflow endpoints
@app.get("/projects/{project_id}/workflows", response_model=List[WorkflowResponse])
async def get_workflows(project_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get all workflows for a project"""
    # Verify project ownership
    project = db.query(Project).filter(Project.id == project_id, Project.user_id == current_user.id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    workflows = db.query(Workflow).filter(Workflow.project_id == project_id).all()
    return workflows

@app.post("/projects/{project_id}/workflows", response_model=WorkflowResponse)
async def create_workflow(project_id: int, workflow: WorkflowCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Create a new workflow"""
    # Verify project ownership
    project = db.query(Project).filter(Project.id == project_id, Project.user_id == current_user.id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    db_workflow = Workflow(
        name=workflow.name,
        description=workflow.description,
        config=workflow.config,
        project_id=project_id
    )
    db.add(db_workflow)
    db.commit()
    db.refresh(db_workflow)
    return db_workflow

@app.post("/workflows/{workflow_id}/execute")
async def execute_workflow(workflow_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Execute a workflow"""
    # Get workflow and verify ownership
    workflow = db.query(Workflow).join(Project).filter(
        Workflow.id == workflow_id,
        Project.user_id == current_user.id
    ).first()
    
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    try:
        # Execute workflow using AWS services
        result = await aws_services.execute_workflow(workflow.config)
        
        # Update workflow status
        workflow.status = "completed"
        db.commit()
        
        return {"status": "success", "result": result}
    except Exception as e:
        workflow.status = "failed"
        db.commit()
        raise HTTPException(status_code=500, detail=f"Workflow execution failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
