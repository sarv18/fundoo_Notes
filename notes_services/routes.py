import json
from fastapi import FastAPI, Depends, HTTPException, Security, Request, Response
from sqlalchemy.orm import Session
from .models import Note, get_db, Label
from .schemas import CreateNote, CreateLabel, AddNoteLabels, AddCollaborators, RemoveCollaborators
from fastapi.security import APIKeyHeader
from .utils import auth_user, RedisUtils, RedisLogRequests
from settings import logger, settings
from redbeat import RedBeatSchedulerEntry
from celery.schedules import crontab
from tasks import celery
from sqlalchemy.orm.attributes import flag_modified
import requests as http
from sqlalchemy import or_


# Initialize FastAPI app with dependency
app = FastAPI(dependencies= [Security(APIKeyHeader(name= "Authorization", auto_error= False)), Depends(auth_user)])

@app.middleware("http")
async def log_requests(request: Request, call_next):
    '''
    Description:
    This middleware logs HTTP requests in your FastAPI application and 
    tracks how many times each API endpoint has been called for a given HTTP method (e.g., GET, POST, PUT, DELETE). 
    Parameters:
    request: An instance of Request from FastAPI, representing the incoming HTTP request.
    call_next: A function that allows the middleware to pass the request to the next handler.
    Returns:
    response: The Response object returned by the next middleware or endpoint handler after processing the request.
    '''
    
    method = request.method  # e.g., GET, POST, etc.
    path = str(request.url.path)  # The requested endpoint
    
    # Initialize Redis log request handler
    redis_instance = RedisLogRequests()

    try:
        # Fetch existing logs from Redis
        logger.info(f"Fetching request logs for method: {method}")
        request_log = redis_instance.get(key=method)
        
        # If existing log is not present, create a new log
        if not request_log:
            logger.info(f"No existing logs found for method: {method}. Creating new log.")
            request_log = {}
        else:
            request_log = json.loads(request_log)
        
        # Update the request count for the path
        if path in request_log:
            request_log[path] += 1
        else:
            request_log[path] = 1
        
        # Save the updated log back to Redis
        logger.info(f"Updating request log for method: {method}, path: {path}")
        redis_instance.save(key=method, value=json.dumps(request_log))
    
    except Exception as e:
        # Log any Redis or other exceptions
        logger.error(f"Error occurred during Redis operation or processing: {e}")
        return Response(content="Internal server error. Please try again later.", status_code=500)

    # Continue processing the request
    try:
        response = await call_next(request)
        logger.info(f"Request processed successfully for path: {path}")
    except Exception as e:
        # Log and handle errors that occur during request processing
        logger.error(f"Error occurred while processing request for path: {path}: {e}")
        return Response(content="Internal server error. Please try again later.", status_code=500)

    return response


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
@app.post("/notes/", status_code= 201)
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

        # If there's a reminder, schedule the reminder email
        if new_note.reminder:
            
            # Reminder timestamp as a string
            reminder_str = new_note.reminder
            task_name = f"reminder_task_{new_note.id}"
        
            entry = RedBeatSchedulerEntry(
                name=task_name,
                task= 'tasks.send_email', 
                schedule= crontab(
                    minute= reminder_str.minute, 
                    hour= reminder_str.hour,
                    day_of_month= reminder_str.day,
                    month_of_year= reminder_str.month
                ),
                app= celery,
                args=(request.state.user["email"], "create_reminder", {'note_id': new_note.id})
            )
            entry.save()

        logger.info(f"Note created successfully for user {user_id}")
        return {
            "message": "Note created successfully",
            "status": "success",
            "data": new_note
        }
        
    except Exception as e:
        logger.exception(f"Error creating note: {e}")
        raise HTTPException(status_code=500, detail="Failed to create note")


# GET all notes
@app.get("/notes/", status_code= 200)
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
        notes_data = RedisUtils.get(key=f"user_{user_id}")
        notes_data = None
        logger.info(f"Notes fetched from cache for user {user_id}")
        source = "cache"

        if not notes_data:
            # If notes are not in cache, fetch from the database
            source = "database"

            # Query to get all notes for the user, eager load labels
            notes = db.query(Note).filter(or_(Note.user_id == user_id, Note.collaborators.has_key(f"{user_id}"))).all()
            
            if not notes:
                # If no notes found in the database
                logger.warning(f"No notes found in the database for user ID: {user_id}")
                raise HTTPException(status_code=404, detail="No notes found")
            
            # Serialize notes and labels to store in cache
            notes_data = [x.to_dict for x in notes]
            logger.info(f"Notes and labels retrieved from Database for user ID: {user_id}")
            
            # Save each note to Redis uniquely using note_id
            for note in notes:
                # Save each note under a unique field in Redis
                RedisUtils.save(key=f"user_{user_id}", field=f"note_{note.id}", value=note.to_dict)
                logger.info(f"Note {note.id} saved to cache for user {user_id}")
            
        else:
            logger.info(f"Notes and labels retrieved from Cache for user ID: {user_id}")

        return {
            "message": f"Got all notes with labels from {source}",    
            "status": "Success",
            "data": notes_data
        }

    except Exception as e:
        logger.error(f"Failed to get all notes for user ID: {user_id}. Error: {str(e)}")
        raise HTTPException(status_code=404, detail="Failed to fetch notes")


# UPDATE Note
@app.put("/notes/{note_id}")
def update_note(request: Request, note_id: int, updated_note: CreateNote, db: Session = Depends(get_db)):
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

        # If there's a reminder, schedule the reminder email
        if note.reminder:
            
            # Reminder timestamp as a string
            reminder_str = note.reminder
            task_name = f"reminder_update_task_{note.id}"
            
            entry = RedBeatSchedulerEntry(
                name=task_name,
                task= 'tasks.send_email', 
                schedule= crontab(
                    minute= reminder_str.minute, 
                    hour= reminder_str.hour,
                    day_of_month= reminder_str.day,
                    month_of_year= reminder_str.month
                ),
                app= celery,
                args=(request.state.user["email"], "update_reminder", {'note_id': note.id})
            )
            entry.save()

        logger.info(f"Note {note_id} updated successfully")
        return {
            "message": "Note updated successfully",
            "status": "success",
            "data": note
        }
    
    # Re-raise known HTTP exceptions like 404
    except HTTPException as http_exc:
        raise http_exc      
    
    except Exception as e:
        logger.error(f"Error updating note {note_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update note")


# DELETE Note
@app.delete("/notes/{note_id}", status_code= 200)
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
        
    # Re-raise known HTTP exceptions like 404
    except HTTPException as http_exc:
        raise http_exc
    
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
    

# ADD Lebels to a note
@app.post("/notes/{note_id}/add-labels/")
def add_labels_to_note( request: Request, label_data: AddNoteLabels, note_id: int, db: Session = Depends(get_db)):
    """
    Description:
    Adds multiple labels to a specific note for the authenticated user.
    Parameters:
    request: Contains the authenticated user information from the JWT token.
    note_id : The ID of the note to which the labels are to be added.
    label_data (List[int]): A list of label IDs to be added to the note.
    db (Session): The database session used to interact with the database.
    Returns:
    dict: A success message along with the updated note details.
    """
    logger.info(f"Adding labels {label_data.label_ids} to note {note_id} for user.")

    # Getting user_id from request state
    user_id = request.state.user["id"]

    # Finding note from database using not id and user id
    note = db.query(Note).filter(Note.id == note_id, Note.user_id == user_id).first()

    # If note not found in database it will raise the exception
    if not note:
        logger.error(f"Note with id {note_id} not found for user {user_id}.")
        raise HTTPException(status_code=404, detail="Note not found")
    
    # Finding labels from database using label id given by user and matching user id
    labels = db.query(Label).filter(Label.id.in_(label_data.label_ids), Label.user_id == user_id).all()
    if len(labels) != len(label_data.label_ids):
        logger.info("Not all labels are found for particular user")
        raise HTTPException(status_code=404, detail="labels not found")
    
    try:
        note.labels.extend(labels)
        db.commit()
        db.refresh(note)
        
        logger.info(f"Labels {label_data.label_ids} added successfully to note {note_id} for user {user_id}.")

        # Store the serialized note with labels in the cache
        RedisUtils.save(key= f"user_{user_id}", field= f"note_{note.id}", value= note.to_dict)
        logger.info(f"Labels {label_data.label_ids} added successfully to  cache with note {note_id} for user {user_id}.")

        # Returning success message
        return{
            "message": f"Lables {label_data.label_ids} added to note_{note_id} successfully",
            "status" : "success",
            "data" : note.labels
        }
        
    except Exception as error:
        logger.error(f"Error while adding labels from note {note_id} for user {user_id}: {error}")
        raise HTTPException(status_code=500, detail="Error for adding labels")


# REMOVE Lebels from note
@app.delete("/notes/{note_id}/remove-labels/")
def remove_labels_from_note(request: Request, label_data: AddNoteLabels, note_id: int, db: Session = Depends(get_db)):
    """
    Description:
    Removes multiple labels from a specific note for the authenticated user.
    Parameters:
    request: Contains the authenticated user information from the JWT token.
    note_id: The ID of the note from which the labels are to be removed.
    label_data : A list of label IDs to be removed from the note.
    db : The database session used to interact with the database.
    Returns:
    dict: A success message along with the updated note details.
    """
     # Getting user_id from request state
    user_id = request.state.user["id"]

    # Finding note from database using not id and user id
    note = db.query(Note).filter(Note.id == note_id, Note.user_id == user_id).first()

    # If note not found in database it will raise the exception
    if not note:
        logger.error(f"Note with id {note_id} not found for user {user_id}.")
        raise HTTPException(status_code=404, detail="Note not found")
    
    # Finding labels from database using label id given by user and matching user id
    labels = db.query(Label).filter(Label.id.in_(label_data.label_ids), Label.user_id == user_id).all()
    
    if not labels:
        logger.info("Not all labels are found for particular user")
        raise HTTPException(status_code=400, detail="labels not found")
    
    try:
        # Checking label for in find labels
        for label in labels:
            # if label are there then delete it
            if label in note.labels:
                note.labels.remove(label)
                logger.info(f"Label {label_data.label_ids} is deleted form the database")

        # Commiting the changes and refreshing database       
        db.commit()
        db.refresh(note)
        logger.info(f"Labels {label_data.label_ids} removed successfully to note {note_id} for user {user_id}.")
        
        # Deleteing labels from note in cache database 
        cached_notes = RedisUtils.get(key= f"user_{user_id}")
        if cached_notes:
            for cached_note in cached_notes:
                if isinstance(cached_note, dict) and cached_note.get("id") == note_id:
                    updated_labels = [lebel for lebel in cached_note['labels'] if lebel["id"] not in label_data.label_ids]
                    cached_note['labels'] = updated_labels 
                    logger.info(f"Labels {label_data.label_ids} removed successfully to note {note_id} for user {user_id}.")

                    # Saving the updated note and lables in cache 
                    RedisUtils.save(key = f"user_{user_id}", field= f"note_{note_id}", value= cached_note)
                    logger.info(f"Labels updated and save successfully to note {note_id} for user {user_id}.")
        
        # Returning the success message
        return {
            "mesaage" : f"Lables {label_data.label_ids} are deleted successfully",
            "status" : "success"
        }
        
    except Exception as error:
        logger.error(f"Error while removing labels from note {note_id} for user {user_id}: {error}")
        raise HTTPException(status_code= 500, detail="Error removing labels")
    
    
# ADD Collaborator to notes    
@app.patch('/notes/add-collaborators', status_code= 200)
def add_collaborators(request : Request, collab_data : AddCollaborators, db : Session = Depends(get_db)):
    """
    Description:
    This function is used for adding collaborators from notes
    Parameters:
    request : The incoming request object.
    collab_data : A AddCollaborator schema add to access user ids.
    db : The database session dependency.
    Return:
    Return the success message with collaborator add from notes
    """
    try:
        # Fetching user id from request.state
        user_id = request.state.user["id"]

        # Fetching note for particular user based on note id provided by user
        note = db.query(Note).filter(Note.id == collab_data.note_id, Note.user_id == user_id).first()
        logger.info(f"Fetching note based Note ID : {collab_data.note_id} and user ID : {user_id}")

        # If note not found
        if not note:
            logger.info(f"Note is not found for note ID : {collab_data.note_id}")
            raise HTTPException(status_code=404, detail=f"Note not found in database for user ID : {user_id} wiht note ID: {collab_data.note_id}")

        # User can not add themselves as collaborator
        if user_id in collab_data.user_ids:
            logger.info(f"User ID {user_id} cannot add themselves as a collaborator.")
            raise HTTPException(status_code=400, detail="You cannot add yourself as a collaborator.") 
        
        # Making HTTP request to user_services to validate the users 
        user_service_url = settings.user_services_url
        response = http.get(user_service_url, params = {"user_ids" : collab_data.user_ids})
       
        # It chaecks the response is not satisfying then raise error
        if response.status_code != 200:
            logger.info(f"Some of the users are not found of user ID : {collab_data.user_ids}")
            raise HTTPException(status_code=400, detail="Some of the uses not found")
        
        # Getting user data in json format form response  
        user_data = response.json()["data"]
        
        # Checking for all user data is retrived from user services or not
        if len(user_data) != len(collab_data.user_ids):
            logger.info("Some of the users are not found from database")
            raise HTTPException("Some of the users are not found from databse")
       
        # Adding user to notes as collaborators.
        for user in user_data:
            note.collaborators[user['id']] = {"email" : user["email"], "access" : collab_data.access}
            logger.info(f"Adding collaborators to notes {note.collaborators}")
        flag_modified(note, "collaborators")    
    
        db.commit()
        db.refresh(note)
        logger.info("Chages are made and saved in database")

        RedisUtils.save(key=f"user_{user_id}", field=f"note_{note.id}", value=note.to_dict)
        logger.info(f"Collaborator {note.collaborators} added successfully to cache with note {note.id} for user {user_id}.")

        # Return the success message
        return{
            "Message" : "Collaborators added successfully.",
            "status" : "Success",
            "Data" : note.collaborators
        }
    
    # Re-raise known HTTP exceptions like 404
    except HTTPException as http_exc:
        raise http_exc
    
    except Exception as error:
        logger.error(f"Unable to add collaborators to note ID : {collab_data.note_id} for user ID : {user_id} ")
        raise HTTPException(status_code=400, detail=f"Unable to add collaborators : {error}")


# Remove collaboraotrs form notes. 
@app.patch('/notes/remove-collaborators', status_code=200)
def remove_collaborators(request: Request, collab_data: RemoveCollaborators, db: Session = Depends(get_db)):
    """
    Description:
    This function is used for removing collaborators from notes
    Parameters:
    request : The incoming request object.
    collab_data : A RemoveCollaborator schema add to access user ids.
    db : The database session dependency.
    Return:
    Return the success message with collaborator remove from notes
    """
    try:
        # Fetching user id from request.state
        user_id = request.state.user["id"]

        # Fetching the note for the particular user based on note id provided by the user
        note = db.query(Note).filter(Note.id == collab_data.note_id, Note.user_id == user_id).first()
        logger.info(f"Fetching note based on Note ID: {collab_data.note_id} and User ID: {user_id}")

        # If note is not found
        if not note:
            logger.info(f"Note not found for Note ID: {collab_data.note_id}")
            raise HTTPException(status_code=404, detail=f"Note not found in database for User ID: {user_id} with Note ID: {collab_data.note_id}")

        # Checking if collaborators exist in the note
        if not note.collaborators:
            logger.info(f"No collaborators found for Note ID: {collab_data.note_id}")
            raise HTTPException(status_code=400, detail="No collaborators found to remove.")


        # Removing specified users from collaborators
        for remove_user_id in collab_data.user_ids:
            # Check if the user is already a collaborator before trying to remove them
            if str(remove_user_id) not in note.collaborators:
                logger.info(f"User with ID {remove_user_id} is not a collaborator")
                raise HTTPException(status_code=400, detail=f"User with ID {remove_user_id} is not a collaborator")

            # Remove the user since they are confirmed to be a collaborator
            note.collaborators.pop(str(remove_user_id))  
            logger.info(f"Removed user with ID {remove_user_id} from collaborators")
        
        # Flagging collaborators field as modified
        flag_modified(note, "collaborators")

        # Commit the changes to the database
        db.commit()
        db.refresh(note)
        logger.info("Changes saved in the database")

        # Cache Invalidation or Update
        cached_notes = RedisUtils.get(key= f"user_{user_id}")
        
        # Deleting collaborators form note in cache
        if cached_notes:
            for cached_note in cached_notes:
                if cached_note["id"] == collab_data.note_id:
                    cached_note["collaborators"] = note.collaborators  
                    logger.info(f"Collaborators updated in cache for Note ID: {collab_data.note_id}")
                    
                    RedisUtils.save(key = f"user_{user_id}", field=f"note_{collab_data.note_id}", value=cached_note)
                    logger.info(f"Updated cache for user {user_id} after removing collaborators")
                    break
        else:
            logger.info(f"No cache found for user {user_id}")

        # Return success message
        return {
            "Message": "Collaborators removed successfully.",
            "status": "Success",
            "Data": note.collaborators
        }

    # Re-raise known HTTP exceptions like 404
    except HTTPException as http_exc:
        raise http_exc

    except Exception as error:
        logger.error(f"Unable to remove collaborators from Note ID: {collab_data.note_id} for User ID: {user_id} : {error}")
        raise HTTPException(status_code=400, detail=f"Unable to remove collaborators: {error}")