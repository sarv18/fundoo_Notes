from .routes import app
from fastapi.testclient import TestClient
from .models import get_db, Base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
import pytest 

# Create engine and session
engine = create_engine("postgresql://postgres:password@localhost/test")
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

client = TestClient(app)

def over_write_get_db():
    db = SessionLocal()
    try:
        yield db 
    finally:
        db.close()

@pytest.fixture
def db_setup():
    Base.metadata.create_all(bind = engine)
    yield 
    Base.metadata.drop_all(bind = engine)

app.dependency_overrides[get_db] = over_write_get_db

# Test successful user registration
def test_user_registration_successful(db_setup):
    data = {
    "email": "user91@example.com",
    "password": "user91@example.com",
    "first_name": "string",
    "last_name": "string"
    }
    response = client.post("/register", json = data)
    assert response.status_code == 201  
    
# Test invalid email 
def test_user_invalid_email(db_setup):
    data = {
    "email": "user91example",
    "password": "user91@example.com",
    "first_name": "string",
    "last_name": "string"
    }
    response = client.post("/register", json = data)
    assert response.status_code == 422
    
# Test invalid password
def test_user_invalid_password(db_setup):
    data = {
    "email": "user91@example.com",
    "password": "user91example",
    "first_name": "string",
    "last_name": "string"
    }
    response = client.post("/register", json = data)
    assert response.status_code == 422
    
# Test invalid first name
def test_user_invalid_first_name(db_setup):
    data = {
    "email": "user91@example.com",
    "password": "user91@example.co",
    "first_name": 123,
    "last_name": "string"
    }
    response = client.post("/register", json = data)
    assert response.status_code == 422
    
# Test invalid last name
def test_user_invalid_last_name(db_setup):
    data = {
    "email": "user91@example.com",
    "password": "user91@example.com",
    "first_name": "string",
    "last_name": 123
    }
    response = client.post("/register", json = data)
    assert response.status_code == 422
    
# Test missing fields
def test_missing_fields(db_setup):
    data = {
    "email": "user91@example.com",
    "password": "user91example",
    "last_name": "string"
    }
    response = client.post("/register", json = data)
    assert response.status_code == 422
    
# To test successful user login
def test_user_login_successful(db_setup):
    # First, create a user to login
    data = {
        "email": "user91@example.com",
        "password": "user91@example.com",
        "first_name": "string",
        "last_name": "string"
    }
    response = client.post("/register", json=data)
    assert response.status_code == 201

    # Now, test login with the same credentials
    login_data = {
        "email": "user91@example.com",
        "password": "user91@example.com"
    }
    response = client.post("/login", json=login_data)
    assert response.status_code == 201
    assert response.json()["message"] == "Login successful"

# To test user login failure (invalid password)
def test_user_login_failure_invalid_password(db_setup):
    # First, create a user
    data = {
        "email": "user92@example.com",
        "password": "user92@example.com",
        "first_name": "string",
        "last_name": "string"
    }
    response = client.post("/register", json=data)
    assert response.status_code == 201

    # Now, test login with an incorrect password
    login_data = {
        "email": "user92@example.com",
        "password": "wrongpassword"
    }
    response = client.post("/login", json=login_data)
    assert response.status_code == 500

# To test user verification
def test_user_verification(db_setup):
    # Register the user
    data = {
        "email": "user93@example.com",
        "password": "user93@example.com",
        "first_name": "string",
        "last_name": "string"
    }
    response = client.post("/register", json=data)
    assert response.status_code == 201

    # Get the verification link from the response
    access_token = response.json()["access_token"]
    
    # Test verification using the token
    response = client.get(f"/verify/{access_token}")
    assert response.status_code == 200
    assert response.json()["message"] == "Email verified successfully!"

# To test fetching users by user_ids
def test_get_users(db_setup):
    # Register two users
    user_1 = {
        "email": "user1@example.com",
        "password": "password@1",
        "first_name": "First",
        "last_name": "User"
    }
    user_2 = {
        "email": "user2@example.com",
        "password": "password@2",
        "first_name": "Second",
        "last_name": "User"
    }
    response_1 = client.post("/register", json=user_1)
    response_2 = client.post("/register", json=user_2)
    #print(response_1.json())
    # Extract user IDs from the registration responses
    user_id_1 = response_1.json()["data"]["id"]
    user_id_2 = response_2.json()["data"]["id"]

   
    # Make the GET request with user IDs in the query string
    response = client.get(f"/users?user_ids={user_id_1}&user_ids={user_id_2}")
    
    # Ensure response status code is 200
    assert response.status_code == 200
    
    # Parse response data
    response_data = response.json()["data"]

    # Check if 2 users are returned
    assert len(response_data) == 2
