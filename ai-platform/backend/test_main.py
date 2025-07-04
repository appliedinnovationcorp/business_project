import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from main import app, get_current_user
from database import get_db, Base
from models import User, Project, Workflow
from auth import get_password_hash

# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

@pytest.fixture
def test_user():
    db = TestingSessionLocal()
    user = User(
        email="test@example.com",
        hashed_password=get_password_hash("testpassword"),
        full_name="Test User",
        company="Test Company"
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    yield user
    db.delete(user)
    db.commit()
    db.close()

@pytest.fixture
def auth_headers(test_user):
    response = client.post("/auth/login", json={
        "email": "test@example.com",
        "password": "testpassword"
    })
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["message"] == "AI Platform API is running"

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_register_user():
    response = client.post("/auth/register", json={
        "email": "newuser@example.com",
        "password": "newpassword",
        "full_name": "New User",
        "company": "New Company"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "newuser@example.com"
    assert data["full_name"] == "New User"
    assert data["company"] == "New Company"

def test_register_duplicate_user():
    # First registration
    client.post("/auth/register", json={
        "email": "duplicate@example.com",
        "password": "password",
        "full_name": "User",
        "company": "Company"
    })
    
    # Second registration with same email
    response = client.post("/auth/register", json={
        "email": "duplicate@example.com",
        "password": "password",
        "full_name": "User",
        "company": "Company"
    })
    assert response.status_code == 400
    assert "Email already registered" in response.json()["detail"]

def test_login_user(test_user):
    response = client.post("/auth/login", json={
        "email": "test@example.com",
        "password": "testpassword"
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_login_invalid_credentials():
    response = client.post("/auth/login", json={
        "email": "test@example.com",
        "password": "wrongpassword"
    })
    assert response.status_code == 401
    assert "Invalid credentials" in response.json()["detail"]

def test_get_dashboard_stats(auth_headers):
    response = client.get("/dashboard/stats", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "total_projects" in data
    assert "active_workflows" in data
    assert "completed_tasks" in data
    assert "ai_services_used" in data

def test_create_project(auth_headers):
    response = client.post("/projects", json={
        "name": "Test Project",
        "description": "A test project",
        "industry": "Technology",
        "objectives": "Test objectives"
    }, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test Project"
    assert data["description"] == "A test project"
    assert data["industry"] == "Technology"

def test_get_projects(auth_headers):
    # Create a project first
    client.post("/projects", json={
        "name": "Test Project",
        "description": "A test project"
    }, headers=auth_headers)
    
    response = client.get("/projects", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert data[0]["name"] == "Test Project"

def test_get_project(auth_headers):
    # Create a project first
    create_response = client.post("/projects", json={
        "name": "Test Project",
        "description": "A test project"
    }, headers=auth_headers)
    project_id = create_response.json()["id"]
    
    response = client.get(f"/projects/{project_id}", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test Project"

def test_create_workflow(auth_headers):
    # Create a project first
    project_response = client.post("/projects", json={
        "name": "Test Project",
        "description": "A test project"
    }, headers=auth_headers)
    project_id = project_response.json()["id"]
    
    response = client.post(f"/projects/{project_id}/workflows", json={
        "name": "Test Workflow",
        "description": "A test workflow",
        "nodes": [{"id": "1", "type": "start"}],
        "edges": []
    }, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test Workflow"
    assert data["description"] == "A test workflow"

def test_get_workflows(auth_headers):
    # Create a project first
    project_response = client.post("/projects", json={
        "name": "Test Project",
        "description": "A test project"
    }, headers=auth_headers)
    project_id = project_response.json()["id"]
    
    # Create a workflow
    client.post(f"/projects/{project_id}/workflows", json={
        "name": "Test Workflow",
        "description": "A test workflow"
    }, headers=auth_headers)
    
    response = client.get(f"/projects/{project_id}/workflows", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert data[0]["name"] == "Test Workflow"

def test_unauthorized_access():
    response = client.get("/projects")
    assert response.status_code == 403

def test_invalid_token():
    headers = {"Authorization": "Bearer invalid_token"}
    response = client.get("/projects", headers=headers)
    assert response.status_code == 401

if __name__ == "__main__":
    pytest.main([__file__])
