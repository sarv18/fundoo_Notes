from celery import Celery
from user_services.utils import send_verification_email
from notes_services.utils import send_note_reminder_email
from asgiref.sync import async_to_sync
from settings import settings, logger

# Initialize Celery instance
celery = Celery(
    __name__, 
    broker=settings.celery_broker, 
    broker_connection_retry_on_startup=True,
    include=["tasks"],
    enable_utc=False
)

# Celery configuration for RedBeat and scheduling
celery.conf.update(
    redbeat_redis_url=settings.redbeat_redis_url,
    redbeat_lock_key=None,  
    beat_max_loop_interval=5, 
    beat_scheduler='redbeat.schedulers.RedBeatScheduler'
)

@celery.task
def send_email(email, email_type, extra_data):
    """
    Description:
    Celery task to send an email, including both verification and reminder emails.
    Parameters:
    email: The recipient's email address.
    email_type: The type of email being sent ('verification' or 'reminder').
    extra_data: Extra data required for the specific email type (e.g., verify_link for verification or note_id for reminder).
    Return:
    str: Status of the task execution.
    """
    logger.info(f"Starting {email_type} email task for {email}")

    try:
        if email_type == "verification":
            verify_link = extra_data
            if not verify_link:
                raise ValueError("Verification link is required for verification email")
            
            # Send verification email
            async_to_sync(send_verification_email)(email, verify_link)
            logger.info(f"Verification email successfully sent to {email}")
        
        elif email_type == "create_reminder":
            note_id = extra_data.get('note_id')
            if not note_id:
                raise ValueError("Note ID is required for create note reminder email")
            
            # Send reminder email
            async_to_sync(send_note_reminder_email)(email, note_id, "create")
            logger.info(f"Reminder email successfully sent to {email}")
        
        elif email_type == "update_reminder":
            note_id = extra_data.get('note_id')
            if not note_id:
                raise ValueError("Note ID is required for update note reminder email")
            
            # Send reminder email
            async_to_sync(send_note_reminder_email)(email, note_id, "update")
            logger.info(f"Reminder email successfully sent to {email}")
        
        else:
            raise ValueError(f"Unsupported email type: {email_type}")
        

    except Exception as e:
        # Log any error that occurs
        logger.error(f"Failed to send {email_type} email to {email}: {str(e)}")
        raise e