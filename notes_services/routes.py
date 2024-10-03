from fastapi import FastAPI, Depends, HTTPException, Security, Request
from sqlalchemy.orm import Session
from .models import Note, get_db,Label
from .schemas import CreateNote, CreateLabel
from fastapi.security import APIKeyHeader
from .utils import auth_user, JwtUtils

# Initialize FastAPI app with dependency
app = FastAPI(dependencies= [Security(APIKeyHeader(name= "Authorization", auto_error= False)), Depends(auth_user)])

@app.get("/")
def read_root():
    '''
    Discription: This is the handler function that gets called when a request is made to the root endpoint
    Parameters: None
    Return: A dictionary with a welcome message.
    '''
    return {"message": "Welcome to the Notes services API!"}


# CREATE Note
@app.post("/notes/")
def create_note(request: Request, note: CreateNote, db: Session = Depends(get_db)):
    '''
    Description: 
    This function creates a new note with the provided title, description and color. The user_id is hardcoded.
    Parameters: 
    note: A `CreateNote` schema instance containing the note details.
    db: The database session to interact with the database.
    Return: 
    The newly created note instance with its details.
'''
    data = note.model_dump()
    data.update(user_id = request.state.user["id"])
    
    new_note = Note(**data)
    
    db.add(new_note)
    db.commit()
    db.refresh(new_note)    
    return {
        "message": "Note created successfully",
        "status": "success",
        "data": new_note
    }


# GET all notes
@app.get("/notes/")
def get_notes(request: Request,  db: Session = Depends(get_db)):
    '''
    Description: 
    This function retrieves a list of notes with pagination (skip and limit).
    Parameters: 
    db: The database session to interact with the database.
    Return: 
    A list of notes within the given range (based on skip and limit).
    '''
    #print(request.state.user)
    user_data = request.state.user
    
    # Get user_id from response
    user_id = user_data["id"] 
    
    # Query notes that belong to the authenticated user
    notes = db.query(Note).filter(Note.user_id == user_id).all()
    
    return {
        "message": "All notes of user",
        "status": "success",
        "data": notes
    }


# UPDATE Note
@app.put("/notes/{note_id}")
def update_note(note_id: int, updated_note: CreateNote, db: Session = Depends(get_db)):
    '''
    Description: 
    This function updates an existing note's details by its ID. If not found, raises a 404 error.
    Parameters: 
    note_id: The ID of the note to update.
    updated_note: A `CreateNote` schema instance containing the updated details.
    db: The database session to interact with the database.
    Return: 
    The updated note object after saving the changes.
    '''
    note = db.query(Note).filter(Note.id == note_id).first()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    
    for key, value in updated_note.model_dump().items():
        setattr(note, key, value)
    
    db.commit()
    db.refresh(note)
    return {
        "message": "Note updated successfully",
        "status": "success",
        "data": note
    }


# DELETE Note
@app.delete("/notes/{note_id}")
def delete_note(note_id: int, db: Session = Depends(get_db)):
    '''
    Description: 
    This function deletes a note by its ID. If not found, raises a 404 error.
    Parameters: 
    note_id: The ID of the note to delete.
    db: The database session to interact with the database.
    Return: 
    A success message confirming the deletion of the note.
    '''

    note = db.query(Note).filter(Note.id == note_id).first()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    
    db.delete(note)
    db.commit()
    return {
        "message": "Note deleted successfully!",
        "status": "success",
        "data": note
        }
    
    
# PATCH API for Archiving a Note
@app.patch("/notes/archive/{note_id}")
def toggle_archive(note_id: int, request: Request, db: Session = Depends(get_db)):
    '''
    Description: 
    Toggle the archive status of a note based on note_id for the authenticated user.
    Parameters: 
    note_id: ID of the note to be toggled.
    request: Contains the authenticated user information.
    db: The database session to interact with the database.
    Return: 
    Updated note with the toggled archive status.
    '''
    user_id = request.state.user["id"]

    # Fetch note based on note_id and user_id
    note = db.query(Note).filter(Note.id == note_id, Note.user_id == user_id).first()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found or not authorized")

    # Toggle the archive status
    note.is_archive = not note.is_archive
    db.commit()
    db.refresh(note)
    return {
        "message": "Archive status toggled", 
        "status": "success",   
        "data": note
        }


# GET API for Retrieving All Archived Notes
@app.get("/notes/archive")
def get_archived_notes(request: Request, db: Session = Depends(get_db)):
    '''
    Description: 
    Fetch all notes of the logged-in user that are archived.
    Parameters: 
    request: Contains the authenticated user information.
    db: The database session to interact with the database.
    Return: 
    List of all archived notes.
    '''
    user_id = request.state.user["id"]

    # Retrieve all notes that are archived for the logged-in user
    archived_notes = db.query(Note).filter(Note.user_id == user_id, Note.is_archive == True, Note.is_trash == False).all()
    return {
        "message": "Archived notes retrieved ",
        "status": "success",
        "data": archived_notes
        }


# PATCH API for Trashing a Note
@app.patch("/notes/trash/{note_id}")
def toggle_trash(note_id: int, request: Request, db: Session = Depends(get_db)):
    '''
    Description: 
    Toggle the trash status of a note based on note_id for the authenticated user.
    Parameters: 
    note_id (int): ID of the note to be toggled.
    request: Contains the authenticated user information.
    db: The database session to interact with the database.
    Return: 
    Updated note with the toggled trash status.
    '''
    user_id = request.state.user["id"]

    # Fetch note based on note_id and user_id
    note = db.query(Note).filter(Note.id == note_id, Note.user_id == user_id).first()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found or not authorized")

    # Toggle the trash status
    note.is_trash = not note.is_trash
    db.commit()
    db.refresh(note)
    return {
        "message": "Trash status toggled",
        "status": "success",
        "data": note
        }


# GET API for Retrieving All Trashed Notes
@app.get("/notes/trash")
def get_trashed_notes(request: Request, db: Session = Depends(get_db)):
    '''
    Description: 
    Fetch all notes of the logged-in user that are in trash.
    Parameters: 
    request: Contains the authenticated user information.
    db: The database session to interact with the database.
    Return: 
    List of all trashed notes.
    '''
    user_id = request.state.user["id"]

    # Retrieve all notes that are in trash for the logged-in user
    trashed_notes = db.query(Note).filter(Note.user_id == user_id, Note.is_trash == True).all()
    return {
        "message": "Trashed notes retrieved",
        "status": "success",
        "data": trashed_notes
        }
    

# CREATE label
@app.post("/labels/")
def create_label(request: Request, label: CreateLabel, db: Session = Depends(get_db)):
    
    try:
        data = label.model_dump()
        data.update(user_id = request.state.user["id"])
        
        new_label = Label(**data)
        
        db.add(new_label)
        db.commit()
        db.refresh(new_label)
        return {
            "message": "Label created successfully",
            "status": "success",
            "data": new_label
        }
    except Exception:
        raise HTTPException(status_code=400, detail= "Failed to create label")
        
    
# GET labels
@app.get("/labels/")
def get_labels(request: Request, db: Session = Depends(get_db)):
    
    try:
        labels = db.query(Label).filter(Label.user_id == request.state.user["id"]).all()
        if not labels:
            return {
                "message": f"No labels found", 
                "status": "success"
                }
             
        return {
            "message" : f"Labes fetched successfully",
            "status": "success",
            "data": labels
        }
    except Exception:
        raise HTTPException(status_code=400, detail="Failed to fetch labels" )
    
# UPDATE label
@app.put("/labels/{label_id}")
def update_label(label_id: int, label: CreateLabel, db: Session= Depends(get_db)):
    
    label_data = db.query(Label).filter(Label.id == label_id).first()
    if not label_data:
        raise HTTPException(status_code=404, detail= f"Lable with ID {label_id} not found")
    
    for key, value in label.model_dump().items():
        setattr(label_data, key, value)
        
    db.commit()
    db.refresh(label_data)
    
    return {
        "message": "Label updated successfully",
        "status": "success",
        "data": label_data  
    }
    
    
# DELETE label
@app.delete("/labels/{label_id}")
def delete_label(label_id: int, db: Session = Depends(get_db)):
    
    label_data = db.query(Label).filter(Label.id == label_id).first()
    if not label_data:
        raise HTTPException(status_code=404, detail= "Label not found")
    
    db.delete(label_data)
    db.commit()
    
    return {
        "message": "Label deleted successfully", 
        "status": "success",
        "data": label_data
    }