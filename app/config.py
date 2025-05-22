from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Database configuration
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/postgres"

    # OpenAI configuration
    OPENAI_API_KEY: str
    MAILCHIMP_TRANSACTIONAL_API_KEY: str
    
    # PureCloud (Genesys Cloud) configuration
    GENESYS_CLOUD_CLIENT_ID: str = ""
    GENESYS_CLOUD_CLIENT_SECRET: str = ""
    GENESYS_OPEN_MESSAGING_DEPLOYMENT_ID: str = ""
    
    # Optional: Add more environment-specific settings
    DEBUG: bool = False

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
