from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    '''
    Discription: Settings class, which is inherited from BaseSettings,
    BaseSettings allows the class to automatically pull in values from environment variables 
    (or from an .env file) and validate those settings.
    '''
    model_config = SettingsConfigDict(env_file= ".env", extra= "ignore")
    db_url: str
    
settings = Settings()