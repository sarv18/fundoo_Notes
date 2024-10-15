from pydantic_settings import BaseSettings, SettingsConfigDict
from loguru import logger

# Loguru Configuration
logger.remove(0)
logger.add("logs/file.log", level= "INFO", rotation= "100 MB")

class Settings(BaseSettings):
    '''
    Description: Settings class, which is inherited from BaseSettings,
    BaseSettings allows the class to automatically pull in values from environment variables 
    (or from an .env file) and validate those settings.
    '''
    model_config = SettingsConfigDict(env_file= ".env", extra= "ignore")
    
    # Database settings
    db_url: str
    notes_db_url: str
    
    # JWT settings
    secret_key: str 
    algorithm: str 
    access_token_expire_minutes: int
    refresh_token_expire_minutes: int
    
     # Email settings
    mail_username: str
    mail_password: str
    mail_from: str
    mail_port: int
    mail_server: str  
    mail_from_name: str
    mail_starttls: bool
    mail_ssl_tls: bool
    use_credentials: bool
    
    # Authentication endpoint
    endpoint: str
    
    # Celery Broker 
    celery_broker: str
    
    # Redbeat redis url
    redbeat_redis_url: str
    
    # User services url
    user_services_url: str
    
    
settings = Settings()