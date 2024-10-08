from celery import Celery
from user_services.utils import send_verification_email
from asgiref.sync import async_to_sync
from settings import settings, logger

# Initialize Celery instance
celery = Celery(__name__, broker= settings.celery_broker, broker_connection_retry_on_startup= True)

@celery.task
def send_mail(email, verify_link):
    """
    Description: Celery task to send a verification email.
    Parameters:
    email: The recipient's email address.
    verify_link: The verification link to be included in the email.
    Return:
    str: Status of the task execution.
    """
    logger.info(f"Starting email task for {email}")
    
    try:
        # Send verification email
        async_to_sync(send_verification_email)(email, verify_link)
        logger.info(f"Verification email successfully sent to {email}")
        
        return "success"
    
    except Exception as e:
        # Log any error that occurs
        logger.error(f"Failed to send verification email to {email}: {str(e)}")
        raise e