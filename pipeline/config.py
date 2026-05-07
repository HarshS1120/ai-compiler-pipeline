"""Base configuration and schemas for the compiler pipeline"""
from typing import List, Dict, Optional, Any
import os

class PipelineConfig:
    """Pipeline configuration"""
    MODEL_NAME = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
    TEMPERATURE = 0.1
    MAX_RETRIES = 3
    MAX_TOKENS = 4000
    
    SCHEMA_DIR = "data/schemas"
    TEST_DIR = "data/tests"
    
    @classmethod
    def ensure_dirs(cls):
        os.makedirs(cls.SCHEMA_DIR, exist_ok=True)
        os.makedirs(cls.TEST_DIR, exist_ok=True)