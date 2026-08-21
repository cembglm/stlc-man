"""
config package
--------------
Application configuration settings
"""

import os
from dotenv import load_dotenv

load_dotenv()

# MongoDB Configuration
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")

# LM Studio / Model Configuration
MODEL_API_BASE_URL = os.getenv("MODEL_API_BASE_URL", "http://localhost:1234")
MODEL_IDENTIFIER = os.getenv("MODEL_IDENTIFIER", "llama-3.2-3b-instruct")
