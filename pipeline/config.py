"""Base configuration and schemas for the compiler pipeline"""
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
import os

class Role(BaseModel):
    name: str
    permissions: List[str]

class Feature(BaseModel):
    name: str
    description: str
    requires_auth: bool = True
    required_role: Optional[str] = None

class Entity(BaseModel):
    name: str
    fields: Dict[str, str]
    relations: List[Dict[str, str]] = []

class IntentSchema(BaseModel):
    """Stage 1 Output: Structured Intent"""
    app_name: str
    app_type: str
    features: List[Feature]
    roles: List[Role]
    entities: List[Entity]
    business_rules: List[str]
    assumptions: List[str] = []

class PageSchema(BaseModel):
    name: str
    route: str
    components: List[str]
    required_role: Optional[str] = None
    api_calls: List[str] = []

class DesignSchema(BaseModel):
    """Stage 2 Output: System Design"""
    pages: List[PageSchema]
    data_flows: List[Dict[str, Any]]
    auth_flows: Dict[str, Any]

class UIComponent(BaseModel):
    type: str
    props: Dict[str, Any] = {}
    events: List[str] = []

class UISchema(BaseModel):
    """Stage 3 Output: UI Configuration"""
    pages: Dict[str, List[UIComponent]]
    layouts: Dict[str, Any]
    theme: Dict[str, str] = {}

class APIEndpoint(BaseModel):
    method: str
    path: str
    request_body: Optional[Dict[str, str]] = None
    response: Dict[str, str]
    auth_required: bool = True
    required_role: Optional[str] = None

class APISchema(BaseModel):
    """Stage 3 Output: API Configuration"""
    endpoints: List[APIEndpoint]
    middleware: List[str] = []

class DBField(BaseModel):
    type: str
    required: bool = True
    unique: bool = False
    default: Optional[Any] = None

class DBSchema(BaseModel):
    """Stage 3 Output: Database Configuration"""
    tables: Dict[str, Dict[str, DBField]]
    relations: List[Dict[str, str]]

class AuthRule(BaseModel):
    role: str
    resource: str
    action: str
    condition: Optional[str] = None

class AuthSchema(BaseModel):
    """Stage 3 Output: Auth Configuration"""
    roles: List[str]
    permissions: List[AuthRule]
    auth_provider: str = "jwt"

class CompleteSchema(BaseModel):
    """Final Output: Complete Application Configuration"""
    intent: IntentSchema
    design: DesignSchema
    ui: UISchema
    api: APISchema
    database: DBSchema
    auth: AuthSchema
    metadata: Dict[str, Any] = {}

class PipelineConfig:
    """Pipeline configuration"""
    MODEL_NAME = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
    TEMPERATURE = 0.1  # Low for determinism
    MAX_RETRIES = 3
    MAX_TOKENS = 4000
    
    SCHEMA_DIR = "data/schemas"
    TEST_DIR = "data/tests"
    
    @classmethod
    def ensure_dirs(cls):
        os.makedirs(cls.SCHEMA_DIR, exist_ok=True)
        os.makedirs(cls.TEST_DIR, exist_ok=True)