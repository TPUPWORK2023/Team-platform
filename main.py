import os
from fastapi import FastAPI
from datetime import datetime
from app.middleware import add_middleware
from app.routes import credit, team, auth
from settings import get_env_config, Environment
import uvicorn
from pathlib import Path
from mangum import Mangum
from dotenv import load_dotenv
from app.domains.create_tables import create_dynamodb_tables
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv(override=True) 

def create_app(env: Environment = Environment.DEVELOPMENT) -> FastAPI:
    """Create a FastAPI application instance.

    Args:
        env (Environment): The environment configuration to use.

    Returns:
        FastAPI: The FastAPI application instance.
    """
    app = FastAPI()
    
    try:
        # Get environment specific config
        env_config = get_env_config(env)
        # Set app configurations
        app.state.config = env_config
        
        # Create DynamoDB tables on startup
        logger.info("Creating DynamoDB tables...")
        create_dynamodb_tables()
        logger.info("DynamoDB tables created successfully!")
        
    except Exception as e:
        logger.error(f"Error during app initialization: {e}")
        app.state.config = {}  # Fallback to empty config

    # Add CORS middleware
    add_middleware(app)
    
    # Include routes
    app.include_router(auth.router, prefix="/auth", tags=["Authentication"]) 
    app.include_router(team.router, prefix="/team", tags=["Team Management"])
    app.include_router(credit.router, prefix="/credits", tags=["Credit Management"])
    
    return app

# Get environment from env variable or default to development
APP_ENV = os.getenv("APP_ENV", Environment.DEVELOPMENT)
app = create_app(APP_ENV)

handler = Mangum(app)

@app.get("/")
async def root():
    
    current_datetime = datetime.now().isoformat()
    return {"message": f"Hello User - {current_datetime}"}

if __name__ == "__main__":
    try:
        uvicorn.run(f"{Path(__file__).stem}:app", host="0.0.0.0", port=8000, env_file=".env", reload=True)
    except Exception as e:
        logger.error(f"Error starting the server: {e}")
 