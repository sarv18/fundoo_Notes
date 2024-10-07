from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    '''
    Discription: Settings class, which is inherited from BaseSettings,
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
settings = Settings()