from fastapi import FastAPI, Depends, HTTPException, Security, Request
from sqlalchemy.orm import Session
from .models import Note, get_db, Label
from .schemas import CreateNote, CreateLabel
from fastapi.security import APIKeyHeader
from .utils import auth_user, RedisUtils
from settings import logger

# Initialize FastAPI app with dependency
app = FastAPI(dependencies= [Security(APIKeyHeader(name= "Authorization", auto_error= False)), Depends(auth_user)])

@app.get("/")
def read_root():
    '''
    Discription: This is the handler function that gets called when a request is made to the root endpoint
    Parameters: None
    Return: A dictionary with a welcome message.
    '''
    logger.info("Root endpoint accessed")
    return {"message": "Welcome to the Notes services API!"}


# CREATE Note
@app.post("/notes/")
def create_note(request: Request, note: CreateNote, db: Session = Depends(get_db)):
    '''
    Description: 
    This function creates a new note with the provided title, description and color,
    and associates it with the authenticated user.
    Parameters: 
    request: The incoming request containing user information.
    note: A `CreateNote` schema instance containing the note details.
    db: The database session to interact with the database.
    Return: 
    dict: A dictionary containing a success message and the newly created note details.
'''
    try:
        data = note.model_dump()
        user_id = request.state.user["id"]
        data.update(user_id=user_id)

        new_note = Note(**data)

        db.add(new_note)
        db.commit()
        db.refresh(new_note)

        # Save note to Redis cache
        RedisUtils.save(key=f"user_{user_id}", field=new_note.id, value=new_note.to_dict)

        logger.info(f"Note created successfully for user {user_id}")
        return {
            "message": "Note created successfully",
            "status": "success",
            "data": new_note
        }
        
    except Exception as e:
        logger.error(f"Error creating note: {e}")
        raise HTTPException(status_code=500, detail="Failed to create note")


# GET all notes
@app.get("/notes/")
def get_notes(request: Request, db: Session = Depends(get_db)):
    '''
    Description: 
    This function retrieves a list of all notes for the authenticated user. 
    It first checks the Redis cache for stored notes; if none are found, it fetches from the database.
    Parameters: 
    request: The incoming request containing user information.
    db: The database session to interact with the database.
    Return: 
    dict: A dictionary containing a success message and a list of notes either from the cache or the database.
    '''
    try:
        user_id = request.state.user["id"]

        # Check Redis cache for notes
        cached_notes = RedisUtils.get(key=f"user_{user_id}")
        if cached_notes:
            logger.info(f"Notes fetched from cache for user {user_id}")
            return {
                "message": "Notes fetched from cache", 
                "status": "success",
                "data": cached_notes
            }

        # Fetch from database if cache is empty
        notes = db.query(Note).filter(Note.user_id == user_id).all()
        if not notes:
            raise HTTPException(status_code=404, detail="No notes found")

        logger.info(f"Notes fetched from database for user {user_id}")
        return {
            "message": "Notes fetched from database",
            "status": "success",
            "data": notes
        }
        
    except Exception as e:
        logger.error(f"Error fetching notes: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch notes")


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
    dict: A dictionary containing a success message and the updated note details.
    '''
    try:
        note = db.query(Note).filter(Note.id == note_id).first()
        if not note:
            raise HTTPException(status_code=404, detail="Note not found")

        for key, value in updated_note.model_dump().items():
            setattr(note, key, value)

        db.commit()
        db.refresh(note)

        # Update note in Redis cache
        RedisUtils.save(key=f"user_{note.user_id}", field=note.id, value=note.to_dict)

        logger.info(f"Note {note_id} updated successfully")
        return {
            "message": "Note updated successfully",
            "status": "success",
            "data": note
        }
        
    except Exception as e:
        logger.error(f"Error updating note {note_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update note")


# DELETE Note
@app.delete("/notes/{note_id}")
def delete_note(request: Request, note_id: int, db: Session = Depends(get_db)):
    '''
    Description: 
    This function deletes a note by its ID. If not found, raises a 404 error.
    Parameters: 
    request: The incoming request containing user information.
    note_id: The ID of the note to delete.
    db: The database session to interact with the database.
    Return: 
    dict: A success message confirming the deletion of the note.
    '''
    try:
        note = db.query(Note).filter(Note.id == note_id).first()
        if not note:
            raise HTTPException(status_code=404, detail="Note not found")

        db.delete(note)
        db.commit()

        # Delete note from Redis cache
        RedisUtils.delete(key=f"user_{request.state.user['id']}", field=note_id)

        logger.info(f"Note {note_id} deleted successfully")
        return {
            "message": "Note deleted successfully",
            "status": "success"
        }
    except Exception as e:
        logger.error(f"Error deleting note {note_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete note")
    
    
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
    dict: A success message along with the updated note details reflecting the archive status.
    '''
    try:
        user_id = request.state.user["id"]
        note = db.query(Note).filter(Note.id == note_id, Note.user_id == user_id).first()
        if not note:
            raise HTTPException(status_code=404, detail="Note not found or not authorized")

        # Toggle archive status
        note.is_archive = not note.is_archive
        db.commit()
        db.refresh(note)
        
        logger.info(f"Note {note_id} archive status toggled for user {user_id}")
        return {
            "message": "Archive status toggled", 
            "status": "success",   
            "data": note
        }
        
    except Exception as e:
        logger.error(f"Error toggling archive status for note {note_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to toggle archive status")


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
    dict: A list of all archived notes.
    '''
    try:
        user_id = request.state.user["id"]
        archived_notes = db.query(Note).filter(Note.user_id == user_id, Note.is_archive == True, Note.is_trash == False).all()
        
        logger.info(f"Archived notes retrieved for user {user_id}")
        return {
            "message": "Archived notes retrieved",
            "status": "success",
            "data": archived_notes
        }
        
    except Exception as e:
        logger.error(f"Error retrieving archived notes: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve archived notes")


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
    dict: A success message along with the updated note details reflecting the trash status.
    '''
    try:
        user_id = request.state.user["id"]
        note = db.query(Note).filter(Note.id == note_id, Note.user_id == user_id).first()
        if not note:
            raise HTTPException(status_code=404, detail="Note not found or not authorized")

        # Toggle trash status
        note.is_trash = not note.is_trash
        db.commit()
        db.refresh(note)
        
        logger.info(f"Note {note_id} trash status toggled for user {user_id}")
        return {
            "message": "Trash status toggled",
            "status": "success",
            "data": note
        }
        
    except Exception as e:
        logger.error(f"Error toggling trash status for note {note_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to toggle trash status")


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
    dict: A list of all trashed notes.
    '''
    try:
        user_id = request.state.user["id"]
        trashed_notes = db.query(Note).filter(Note.user_id == user_id, Note.is_trash == True).all()
        
        logger.info(f"Trashed notes retrieved for user {user_id}")
        return {
            "message": "Trashed notes retrieved",
            "status": "success",
            "data": trashed_notes
        }
        
    except Exception as e:
        logger.error(f"Error retrieving trashed notes: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve trashed notes")
    

# CREATE label
@app.post("/labels/")
def create_label(request: Request, label: CreateLabel, db: Session = Depends(get_db)):
    '''
    Description:
    This function creates a new label with the provided name and color for the authenticated user.
    Parameters:
    request: Contains the authenticated user information from the JWT token.
    label: A `CreateLabel` schema instance containing the label details (name, color).
    db: The database session to interact with the database.
    Return:
    dict: A success message and the newly created label instance or raise exception.
    '''
    try:
        data = label.model_dump()
        data.update(user_id=request.state.user["id"])
        new_label = Label(**data)
        
        db.add(new_label)
        db.commit()
        db.refresh(new_label)
        
        logger.info(f"Label {new_label.id} created for user {request.state.user['id']}")
        return {
            "message": "Label created successfully",
            "status": "success",
            "data": new_label
        }
    except Exception as e:
        logger.error(f"Error creating label: {e}")
        raise HTTPException(status_code=500, detail="Failed to create label")
        
    
# GET labels
@app.get("/labels/")
def get_labels(request: Request, db: Session = Depends(get_db)):
    '''
    Description:
    This function retrieves all labels created by the authenticated user.
    Parameters:
    request: Contains the authenticated user information from the JWT token.
    db: The database session to interact with the database.
    Return:
    dict: A success message and a list of all labels created by the user.
    '''
    try:
        labels = db.query(Label).filter(Label.user_id == request.state.user["id"]).all()
        if not labels:
            logger.info(f"No labels found for user {request.state.user['id']}")
            return {
                "message": "No labels found",
                "status": "success"
            }
            
        logger.info(f"Labels retrieved for user {request.state.user['id']}")
        return {
            "message": "Labels fetched successfully",
            "status": "success",
            "data": labels
        }
        
    except Exception as e:
        logger.error(f"Error fetching labels: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch labels")
    
    
# UPDATE label
@app.put("/labels/{label_id}")
def update_label(label_id: int, label: CreateLabel, db: Session= Depends(get_db)):
    '''
    Description:
    This function updates an existing label's details (name, color) based on its ID. If the label is not found, a 404 error is raised.
    Parameters:
    label_id: The ID of the label to update.
    label: A `CreateLabel` schema instance containing the updated label details (name, color).
    db: The database session to interact with the database.
    Return:
    dict: A success message and the updated label instance.
    '''
    try:
        label_data = db.query(Label).filter(Label.id == label_id).first()
        if not label_data:
            raise HTTPException(status_code=404, detail="Label not found")
        
        for key, value in label.model_dump().items():
            setattr(label_data, key, value)
        
        db.commit()
        db.refresh(label_data)
        
        logger.info(f"Label {label_id} updated successfully")
        return {
            "message": "Label updated successfully",
            "status": "success",
            "data": label_data
        }
        
    except Exception as e:
        logger.error(f"Error updating label {label_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update label")
    
    
# DELETE label
@app.delete("/labels/{label_id}")
def delete_label(label_id: int, db: Session = Depends(get_db)):
    '''
    Description:
    This function deletes a label by its ID. If the label is not found, a 404 error is raised.
    Parameters:
    label_id: The ID of the label to delete.
    db: The database session to interact with the database.
    Return:
    A success message confirming the deletion of the label.
    '''
    try:
        # Fetch label by ID
        label_data = db.query(Label).filter(Label.id == label_id).first()
        
        if not label_data:
            logger.error(f"Label with ID {label_id} not found.")
            raise HTTPException(status_code=404, detail="Label not found")
        
        # Delete the label
        db.delete(label_data)
        db.commit()
        
        logger.info(f"Label with ID {label_id} deleted successfully.")
        return {
            "message": "Label deleted successfully", 
            "status": "success"
        }
    except Exception as e:
        logger.error(f"Error while deleting label with ID {label_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete label")
    