"""Entry point for FastAPI server."""

import logging
import uvicorn
from .config import Config
from .api_server import create_api_server

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Run the FastAPI server."""
    # Validate configuration
    config = Config()
    errors = config.validate()
    
    if errors:
        logger.error("Configuration errors:")
        for error in errors:
            logger.error(f"  - {error}")
        logger.error("Please check your .env file")
        return
    
    logger.info(f"Starting GitHub Automation Agent API")
    logger.info(f"Repository: {config.get_repo_full_name()}")
    logger.info(f"LLM Provider: {config.LLM_PROVIDER}")
    
    # Create FastAPI app
    app = create_api_server(config)
    
    # Run with uvicorn
    uvicorn.run(
        app,
        host=config.HOST,
        port=config.PORT,
        log_level="info"
    )


if __name__ == "__main__":
    main()
