from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from .models import Base, get_db
from .routes import app
import pytest
import responses


# Create a TestClient instance
client = TestClient(app)

# Set up the test database
engine = create_engine("postgresql://postgres:password@localhost/test")
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Override the get_db dependency
def override_get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def db_setup():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture
def auth_user_mock():
    responses.add(
        responses.GET,
        "http://127.0.0.1:8000/user/eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyOTFAZXhhbXBsZS5jb20iLCJ1c2VyX2lkIjoxfQ._XsC7qgHEpBvaZbzPmgDOOPnDUw9W6_UCpNDyhlgA-8",
        json= {
            "message": "Authorizaton successful",
            "status": "success",
            "data": {
                    "id": 1,
                    "email": "user91@example.com",
                    "first_name": "string",
                    "last_name": "string",
                    "is_verified": True,
                }
        },
        status=200
    )

@pytest.fixture
def get_user_mock():
    responses.add(
        responses.GET,
        "http://127.0.0.1:8000/users?user_ids=2",
        json= {
            "message" : "User found successfully.", 
            "status" : "Success",
            "data" : [
                {
                "id": 2,
                "email": "sarvesh@test.com",
                "first_name": "Sarvesh",
                "last_name": "Shelke",
                "is_verified": False,
                "created_at": "2024-09-26T12:38:17.482027",
                "updated_at": "2024-09-26T12:38:17.482027"
                }
            ]
        },
        status=200
    )

# Test case for creating a successful note with mocked external API
@responses.activate
def test_create_note_successful(db_setup, auth_user_mock):
    
    # Payload for creating a note
    data = {
        "title": "string",
        "description": "string",
        "color": "string",
        "is_archive": False,
        "is_trash": False,
        "reminder": "2024-10-16T21:15:38.710831"
        }

    # Call the create note API
    response = client.post("/notes/", json=data, headers= {"Authorization": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyOTFAZXhhbXBsZS5jb20iLCJ1c2VyX2lkIjoxfQ._XsC7qgHEpBvaZbzPmgDOOPnDUw9W6_UCpNDyhlgA-8"})
        
    # Assert the response status code and content
    assert response.status_code == 201
    
# Test case for create note invalid fields
@responses.activate
def test_create_note_invalid_field(db_setup, auth_user_mock):
    
    # Payload for creating a note
    data = {
        "title": 123,
        "description": 123,
        "color": "string",
        "is_archive": False,
        "is_trash": False,
        "reminder": "2024-10-16T21:15:38.710831"
        }

    # Call the create note API
    response = client.post("/notes/", json=data, headers= {"Authorization": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyOTFAZXhhbXBsZS5jb20iLCJ1c2VyX2lkIjoxfQ._XsC7qgHEpBvaZbzPmgDOOPnDUw9W6_UCpNDyhlgA-8"})
        
    # Assert the response status code and content
    assert response.status_code == 422 
    
# Test case for ceate note missing fields
@responses.activate
def test_create_note_missing_field(db_setup, auth_user_mock):
    
    # Payload for creating a note
    data = {
        "description": "string",
        "color": "string",
        "is_archive": False,
        "is_trash": False
        }

    # Call the create note API
    response = client.post("/notes/", json=data, headers= {"Authorization": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyOTFAZXhhbXBsZS5jb20iLCJ1c2VyX2lkIjoxfQ._XsC7qgHEpBvaZbzPmgDOOPnDUw9W6_UCpNDyhlgA-8"})
        
    # Assert the response status code and content
    assert response.status_code == 422
    
# Test case for getting all notes successfully
@responses.activate
def test_get_all_notes_successful(db_setup, auth_user_mock):

    # Add notes to the database setup
    note1 = {
        "title": "Test Note 1",
        "description": "Description 1",
        "color": "blue",
        "is_archive": False,
        "is_trash": False,
        "reminder": "2024-10-16T21:15:38.710831"
    }
    note2 = {
        "title": "Test Note 2",
        "description": "Description 2",
        "color": "red",
        "is_archive": False,
        "is_trash": False,
        "reminder": "2024-10-16T21:20:38.710831"
    }

    # Insert notes through API (assuming POST works correctly)
    client.post("/notes/", json=note1, headers={"Authorization": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyOTFAZXhhbXBsZS5jb20iLCJ1c2VyX2lkIjoxfQ._XsC7qgHEpBvaZbzPmgDOOPnDUw9W6_UCpNDyhlgA-8"})
    client.post("/notes/", json=note2, headers={"Authorization": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyOTFAZXhhbXBsZS5jb20iLCJ1c2VyX2lkIjoxfQ._XsC7qgHEpBvaZbzPmgDOOPnDUw9W6_UCpNDyhlgA-8"})

    # Call the GET all notes API
    response = client.get("/notes/", headers={"Authorization": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyOTFAZXhhbXBsZS5jb20iLCJ1c2VyX2lkIjoxfQ._XsC7qgHEpBvaZbzPmgDOOPnDUw9W6_UCpNDyhlgA-8"})

    # Assert the response status code and content
    assert response.status_code == 200

# Test case for no notes found
@responses.activate
def test_get_all_notes_no_notes(db_setup, auth_user_mock):

    # No notes are present in the database setup

    # Call the GET all notes API
    response = client.get("/notes/", headers={"Authorization": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyOTFAZXhhbXBsZS5jb20iLCJ1c2VyX2lkIjoxfQ._XsC7qgHEpBvaZbzPmgDOOPnDUw9W6_UCpNDyhlgA-8"})

    # Assert the response status code and content
    assert response.status_code == 404
    
    
# Test case for successfully updating a note
@responses.activate
def test_update_note_successful(db_setup, auth_user_mock):
    
    # Step 1: Create a note to be updated
    initial_note = {
        "title": "Initial Note",
        "description": "Initial Description",
        "color": "yellow",
        "is_archive": False,
        "is_trash": False,
        "reminder": "2024-10-16T21:15:38.710831"
    }
    
    # Insert the note via the API
    create_response = client.post("/notes/", json=initial_note, headers={"Authorization": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyOTFAZXhhbXBsZS5jb20iLCJ1c2VyX2lkIjoxfQ._XsC7qgHEpBvaZbzPmgDOOPnDUw9W6_UCpNDyhlgA-8"})
    assert create_response.status_code == 201
    
    note_id = create_response.json()["data"]["id"]  # Extract note_id from the response
    
    # Step 2: Define the updated note payload
    updated_note = {
        "title": "Updated Note",
        "description": "Updated Description",
        "color": "blue",
        "is_archive": False,
        "is_trash": False,
        "reminder": "2024-10-20T15:30:00"
    }

    # Step 3: Call the PUT API to update the note
    response = client.put(f"/notes/{note_id}", json=updated_note, headers={"Authorization": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyOTFAZXhhbXBsZS5jb20iLCJ1c2VyX2lkIjoxfQ._XsC7qgHEpBvaZbzPmgDOOPnDUw9W6_UCpNDyhlgA-8"})

    # Step 4: Assert the response
    assert response.status_code == 200
    
# Test case for updating a non-existent note (404 error)
@responses.activate
def test_update_note_not_found(db_setup, auth_user_mock):
    
    # Define the payload for the update
    updated_note = {
        "title": "Updated Note",
        "description": "Updated Description",
        "color": "blue",
        "is_archive": False,
        "is_trash": False,
        "reminder": "2024-10-20T15:30:00"
    }

    # Call the PUT API for a note ID that does not exist
    response = client.put("/notes/9999", json=updated_note, headers={"Authorization": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyOTFAZXhhbXBsZS5jb20iLCJ1c2VyX2lkIjoxfQ._XsC7qgHEpBvaZbzPmgDOOPnDUw9W6_UCpNDyhlgA-8"})

    # Assert the response
    assert response.status_code == 404

# Test case for successful note delete
@responses.activate
def test_delete_note_success(db_setup, auth_user_mock):
    
    # Step 1: Create a note to be updated
    initial_note = {
        "title": "Initial Note",
        "description": "Initial Description",
        "color": "yellow",
        "is_archive": False,
        "is_trash": False,
        "reminder": "2024-10-16T21:15:38.710831"
    }
    
    # Insert the note via the API
    create_response = client.post("/notes/", json=initial_note, headers={"Authorization": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyOTFAZXhhbXBsZS5jb20iLCJ1c2VyX2lkIjoxfQ._XsC7qgHEpBvaZbzPmgDOOPnDUw9W6_UCpNDyhlgA-8"})
    assert create_response.status_code == 201
    
    note_id = create_response.json()["data"]["id"]  # Extract note_id from the response
    
    # Call the delete note API
    response = client.delete(f"/notes/{note_id}", headers={"Authorization": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyOTFAZXhhbXBsZS5jb20iLCJ1c2VyX2lkIjoxfQ._XsC7qgHEpBvaZbzPmgDOOPnDUw9W6_UCpNDyhlgA-8"})
    print(response.json())
    print(f"Headers: {response.request.headers}")
    # Assert the response status code and content
    assert response.status_code == 200

# Test Case for Trying to Delete a Non-Existent Note
@responses.activate
def test_delete_note_not_found(db_setup, auth_user_mock):
    # Note ID that doesn't exist
    note_id = 999
    
    # Call the delete note API
    response = client.delete(f"/notes/{note_id}", headers={"Authorization": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyOTFAZXhhbXBsZS5jb20iLCJ1c2VyX2lkIjoxfQ._XsC7qgHEpBvaZbzPmgDOOPnDUw9W6_UCpNDyhlgA-8"})
    print(response.json())
    # Assert the response status code and content
    assert response.status_code == 404


# Test case for adding collaborators successfully
@responses.activate
def test_add_collaborators_success(db_setup, auth_user_mock, get_user_mock):
    
    initial_note = {
        "title": "Initial Note",
        "description": "Initial Description",
        "color": "yellow",
        "is_archive": False,
        "is_trash": False,
        "reminder": "2024-10-16T21:15:38.710831"
    }
    
    # Insert the note via the API
    create_response = client.post("/notes/", json=initial_note, headers={"Authorization": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyOTFAZXhhbXBsZS5jb20iLCJ1c2VyX2lkIjoxfQ._XsC7qgHEpBvaZbzPmgDOOPnDUw9W6_UCpNDyhlgA-8"})
    assert create_response.status_code == 201
    
    note_id = create_response.json()["data"]["id"]

    # Payload for adding collaborators
    data = {
        "note_id": note_id,  
        "user_ids": [2],  
        "access": "readonly"
    }

    # Call the add collaborators API
    response = client.patch("/notes/add-collaborators", json=data, headers={"Authorization": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyOTFAZXhhbXBsZS5jb20iLCJ1c2VyX2lkIjoxfQ._XsC7qgHEpBvaZbzPmgDOOPnDUw9W6_UCpNDyhlgA-8"})
    print(f"Response content: {response.json()}")
    
    assert response.status_code == 200

# Test case for adding self as collaborator (should fail)
@responses.activate
def test_add_self_as_collaborator(db_setup, auth_user_mock, get_user_mock):
    initial_note = {
        "title": "Initial Note",
        "description": "Initial Description",
        "color": "yellow",
        "is_archive": False,
        "is_trash": False,
        "reminder": "2024-10-16T21:15:38.710831"
    }
    
    # Insert the note via the API
    create_response = client.post("/notes/", json=initial_note, headers={"Authorization": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyOTFAZXhhbXBsZS5jb20iLCJ1c2VyX2lkIjoxfQ._XsC7qgHEpBvaZbzPmgDOOPnDUw9W6_UCpNDyhlgA-8"})
    assert create_response.status_code == 201
    
    note_id = create_response.json()["data"]["id"]
    
    # Payload where user tries to add themselves as a collaborator
    data = {
        "note_id": note_id,  
        "user_ids": [46], 
        "access": "readonly"
    }

    # Call the add collaborators API
    response = client.patch("/notes/add-collaborators", json=data, headers={"Authorization": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyOTFAZXhhbXBsZS5jb20iLCJ1c2VyX2lkIjoxfQ._XsC7qgHEpBvaZbzPmgDOOPnDUw9W6_UCpNDyhlgA-8"})

    # Assert the response status code and error message
    assert response.status_code == 400


# Test case for note not found
@responses.activate
def test_add_collaborators_note_not_found(db_setup, auth_user_mock, get_user_mock):
    
    # Payload for adding collaborators to a non-existent note
    data = {
        "note_id": 999,  
        "user_ids": [2],  
        "access": "readonly"
    }

    # Call the add collaborators API
    response = client.patch("/notes/add-collaborators", json=data, headers={"Authorization": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyOTFAZXhhbXBsZS5jb20iLCJ1c2VyX2lkIjoxfQ._XsC7qgHEpBvaZbzPmgDOOPnDUw9W6_UCpNDyhlgA-8" })

    # Assert the response status code and error message
    assert response.status_code == 404


# Test case for invalid user IDs (some users not found)
@responses.activate
def test_add_collaborators_invalid_users(db_setup, auth_user_mock, get_user_mock):
    
    initial_note = {
        "title": "Initial Note",
        "description": "Initial Description",
        "color": "yellow",
        "is_archive": False,
        "is_trash": False,
        "reminder": "2024-10-16T21:15:38.710831"
    }
    
    # Insert the note via the API
    create_response = client.post("/notes/", json=initial_note, headers={"Authorization": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyOTFAZXhhbXBsZS5jb20iLCJ1c2VyX2lkIjoxfQ._XsC7qgHEpBvaZbzPmgDOOPnDUw9W6_UCpNDyhlgA-8"})
    assert create_response.status_code == 201
    
    note_id = create_response.json()["data"]["id"]
    
    # Payload for adding invalid user IDs as collaborators
    data = {
        "note_id": note_id,  
        "user_ids": [999, 1000],  # Non-existent user IDs
        "access": "readonly"
    }

    # Call the add collaborators API
    response = client.patch("/notes/add-collaborators", json=data, headers={"Authorization": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyOTFAZXhhbXBsZS5jb20iLCJ1c2VyX2lkIjoxfQ._XsC7qgHEpBvaZbzPmgDOOPnDUw9W6_UCpNDyhlgA-8"})

    # Assert the response status code and error message
    assert response.status_code == 400
    

# Test case for Successfully Remove Collaborators
@responses.activate
def test_remove_collaborators_success(db_setup, auth_user_mock, get_user_mock):
    # Initial note with collaborators
    initial_note = {
        "title": "Test Note",
        "description": "This is a test note.",
        "color": "blue",
        "is_archive": False,
        "is_trash": False,
        "reminder": "2024-10-18T21:00:00"
    }

    # Create a note
    create_response = client.post("/notes/", json=initial_note, headers={"Authorization": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyOTFAZXhhbXBsZS5jb20iLCJ1c2VyX2lkIjoxfQ._XsC7qgHEpBvaZbzPmgDOOPnDUw9W6_UCpNDyhlgA-8"})
    assert create_response.status_code == 201
    note_id = create_response.json()["data"]["id"]

    # Add collaborators first
    add_collaborators_data = {
        "note_id": note_id,
        "user_ids": [2],
        "access": "readonly"
    }
    client.patch("/notes/add-collaborators", json=add_collaborators_data, headers={"Authorization": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyOTFAZXhhbXBsZS5jb20iLCJ1c2VyX2lkIjoxfQ._XsC7qgHEpBvaZbzPmgDOOPnDUw9W6_UCpNDyhlgA-8"})
    
    # Remove collaborators from note
    remove_data = {
        "note_id": note_id,
        "user_ids": [2]
    }
    
    response = client.patch("/notes/remove-collaborators", json=remove_data, headers={"Authorization": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyOTFAZXhhbXBsZS5jb20iLCJ1c2VyX2lkIjoxfQ._XsC7qgHEpBvaZbzPmgDOOPnDUw9W6_UCpNDyhlgA-8"})
    
    # Assert success
    assert response.status_code == 200
    
    
# Test Case to Remove Collaborators When They Don’t Exist
@responses.activate
def test_remove_collaborators_not_found(db_setup, auth_user_mock, get_user_mock):
    # Initial note
    initial_note = {
        "title": "Test Note",
        "description": "This is a test note.",
        "color": "green",
        "is_archive": False,
        "is_trash": False,
        "reminder": "2024-10-18T21:00:00"
    }

    # Create a note
    create_response = client.post("/notes/", json=initial_note, headers={"Authorization": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyOTFAZXhhbXBsZS5jb20iLCJ1c2VyX2lkIjoxfQ._XsC7qgHEpBvaZbzPmgDOOPnDUw9W6_UCpNDyhlgA-8"})
    assert create_response.status_code == 201
    note_id = create_response.json()["data"]["id"]

    # Remove non-existent collaborators from note
    remove_data = {
        "note_id": note_id,
        "user_ids": [999]  # User ID 999 doesn't exist
    }
    
    response = client.patch("/notes/remove-collaborators", json=remove_data, headers={"Authorization": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyOTFAZXhhbXBsZS5jb20iLCJ1c2VyX2lkIjoxfQ._XsC7qgHEpBvaZbzPmgDOOPnDUw9W6_UCpNDyhlgA-8"})
    
    # Assert failure
    assert response.status_code == 400

#Test Case Remove Collaborators From a Non-Existent Note
@responses.activate
def test_remove_collaborators_note_not_found(db_setup, auth_user_mock, get_user_mock):
    # Attempt to remove collaborators from a non-existent note
    remove_data = {
        "note_id": 9999,  # Invalid note ID
        "user_ids": [2]
    }
    
    response = client.patch("/notes/remove-collaborators", json=remove_data, headers={"Authorization": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyOTFAZXhhbXBsZS5jb20iLCJ1c2VyX2lkIjoxfQ._XsC7qgHEpBvaZbzPmgDOOPnDUw9W6_UCpNDyhlgA-8"})
    
    # Assert failure
    assert response.status_code == 404


#Test Case to Remove Collaborators With No Collaborators in Note
@responses.activate
def test_remove_collaborators_no_collaborators(db_setup, auth_user_mock):
    # Initial note without collaborators
    initial_note = {
        "title": "Test Note",
        "description": "This is a test note.",
        "color": "red",
        "is_archive": False,
        "is_trash": False,
        "reminder": "2024-10-18T21:00:00"
    }

    # Create a note
    create_response = client.post("/notes/", json=initial_note, headers={"Authorization": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyOTFAZXhhbXBsZS5jb20iLCJ1c2VyX2lkIjoxfQ._XsC7qgHEpBvaZbzPmgDOOPnDUw9W6_UCpNDyhlgA-8"})
    assert create_response.status_code == 201
    note_id = create_response.json()["data"]["id"]

    # Attempt to remove collaborators from a note without any collaborators
    remove_data = {
        "note_id": note_id,
        "user_ids": [2]
    }
    
    response = client.patch("/notes/remove-collaborators", json=remove_data, headers={"Authorization": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyOTFAZXhhbXBsZS5jb20iLCJ1c2VyX2lkIjoxfQ._XsC7qgHEpBvaZbzPmgDOOPnDUw9W6_UCpNDyhlgA-8"})
    
    # Assert failure
    assert response.status_code == 400