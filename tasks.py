from celery import Celery
from user_services.utils import send_verification_email
from asgiref.sync import async_to_sync
from settings import settings

# Initialize Celery instance
celery = Celery(__name__, broker= settings.celery_broker, broker_connection_retry_on_startup= True)

@celery.task
def send_mail(email, verify_link):
    
    async_to_sync(send_verification_email)(email, verify_link)
    return "success"