"""Stage 1: Intent Extraction - Natural Language to Structured Intent"""
import json
from typing import Dict, Any, List
from pipeline.base import PipelineStage
from pipeline.utils.llm import LLMHelper
from pipeline.config import IntentSchema, Feature, Role, Entity

class IntentExtractor(PipelineStage):
    """Extracts structured intent from natural language prompts"""
    
    def __init__(self):
        super().__init__("IntentExtractor")
        self.llm = LLMHelper()
    
    def process(self, user_prompt: str) -> Dict[str, Any]:
        """Extract intent from user prompt"""
        
        # Build the extraction prompt
        system_prompt = self._get_system_prompt()
        extraction_prompt = self._build_extraction_prompt(user_prompt)
        
        # Call LLM
        result = self.llm.complete_with_retry(
            system_prompt=system_prompt,
            user_prompt=extraction_prompt,
            temperature=0.1,
            max_tokens=2000
        )
        
        # Validate the extracted intent
        validated = self._validate_intent(result)
        
        return validated
    
    def _get_system_prompt(self) -> str:
        return """You are an expert system analyst. Your job is to extract structured requirements from natural language descriptions of software applications.

You MUST respond with ONLY valid JSON. No explanations, no markdown, just the JSON object.

Follow this EXACT schema:
{
  "app_name": "string - descriptive name for the application",
  "app_type": "string - type of app (CRM, E-commerce, SaaS, Dashboard, etc.)",
  "features": [
    {
      "name": "string - feature name",
      "description": "string - brief description",
      "requires_auth": boolean,
      "required_role": "string or null - role needed to access"
    }
  ],
  "roles": [
    {
      "name": "string - role name",
      "permissions": ["string - permission1", "permission2"]
    }
  ],
  "entities": [
    {
      "name": "string - entity name",
      "fields": {
        "field_name": "data_type (string, integer, boolean, datetime, etc.)"
      },
      "relations": [
        {
          "type": "belongs_to|has_many|many_to_many",
          "entity": "string - related entity name"
        }
      ]
    }
  ],
  "business_rules": [
    "string - business rule description"
  ],
  "assumptions": [
    "string - any assumptions made during extraction"
  ]
}

Rules:
1. Every feature must have a clear description
2. Roles must have at least one permission
3. Entities must have at least one field
4. If something is unclear, make reasonable assumptions and document them in "assumptions"
5. All field names should be in snake_case
6. Data types should be standard (string, integer, boolean, datetime, float, text)
7. Include an "admin" role if any feature mentions admin functionality
8. Include a basic "user" role for any application with authentication"""
    
    def _build_extraction_prompt(self, user_prompt: str) -> str:
        return f"""Extract the complete structured intent from this application description:

USER PROMPT: "{user_prompt}"

Identify:
- What type of application is this?
- What features are requested?
- What roles/users are needed?
- What data entities can you identify?
- What business rules are implied?
- What assumptions are you making?

Remember: Output ONLY valid JSON, nothing else."""
    
    def _validate_intent(self, extracted: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and fix the extracted intent"""
        
        # Check for errors from LLM
        if "error" in extracted:
            return self._create_default_intent(extracted)
        # Handle case where extracted is None or empty
        if not extracted or extracted == {}:
            return self._create_default_intent({"error": "Empty response from LLM"})

        # Handle raw_output (when JSON parsing fails)
        if "raw_output" in extracted:
            # Try to extract what we can from raw text
            raw = extracted.get("raw_output", "")
            print(f"⚠️  LLM returned raw text, attempting extraction...")
            # Try to extract JSON from raw text
            import re
            json_match = re.search(r'\{.*\}', raw, re.DOTALL)
            if json_match:
                try:
                    extracted = json.loads(json_match.group())
                except:
                    pass
        
        # Ensure required fields exist
        required_fields = ["app_name", "app_type", "features", "roles", "entities", "business_rules"]
        for field in required_fields:
            if field not in extracted:
                extracted[field] = []
        
        # Ensure features are properly structured
        if "features" in extracted:
            for i, feature in enumerate(extracted["features"]):
                if isinstance(feature, str):
                    # Convert string feature to proper structure
                    extracted["features"][i] = {
                        "name": feature.lower().replace(" ", "_"),
                        "description": feature,
                        "requires_auth": True,
                        "required_role": None
                    }
                elif isinstance(feature, dict):
                    feature.setdefault("requires_auth", True)
                    feature.setdefault("required_role", None)
                    feature.setdefault("description", feature.get("name", ""))
        
        # Ensure roles are properly structured
        if "roles" in extracted:
            for i, role in enumerate(extracted["roles"]):
                if isinstance(role, str):
                    extracted["roles"][i] = {
                        "name": role.lower().replace(" ", "_"),
                        "permissions": ["read"]
                    }
                elif isinstance(role, dict):
                    role.setdefault("permissions", ["read"])
        
        # Ensure entities are properly structured
        if "entities" in extracted:
            for i, entity in enumerate(extracted["entities"]):
                if isinstance(entity, str):
                    extracted["entities"][i] = {
                        "name": entity.lower().replace(" ", "_"),
                        "fields": {"name": "string", "id": "integer"},
                        "relations": []
                    }
                elif isinstance(entity, dict):
                    entity.setdefault("fields", {"id": "integer"})
                    entity.setdefault("relations", [])
        
        # Add assumptions field
        if "assumptions" not in extracted:
            extracted["assumptions"] = []
        
        # Add default assumptions
        extracted["assumptions"].extend([
            "Standard CRUD operations for all entities",
            "JWT-based authentication",
            "RESTful API design"
        ])
        
        # Generate app_name if missing
        if not extracted.get("app_name"):
            extracted["app_name"] = extracted.get("app_type", "Application")
        
        return extracted
    
    def _create_default_intent(self, error_result: Dict) -> Dict[str, Any]:
        """Create a default intent when extraction fails"""
        error_msg = str(error_result.get("error", "Unknown error"))
        raw = error_result.get("raw_output", "")
        
        # Try one more time to extract meaningful data from raw output
        if raw:
            # Extract any app-like words
            import re
            app_types = re.findall(r'(CRM|e-commerce|dashboard|blog|marketplace|social media|platform|app|system|tool|website)', raw, re.IGNORECASE)
            app_type = app_types[0] if app_types else "Web Application"
        else:
            app_type = "Web Application"
        
        return {
            "app_name": f"{app_type} System",
            "app_type": app_type,
            "features": [
                {
                    "name": "authentication",
                    "description": "User authentication and authorization",
                    "requires_auth": True,
                    "required_role": None
                },
                {
                    "name": "dashboard",
                    "description": "Main dashboard view",
                    "requires_auth": True,
                    "required_role": None
                }
            ],
            "roles": [
                {
                    "name": "user",
                    "permissions": ["read", "write"]
                },
                {
                    "name": "admin",
                    "permissions": ["read", "write", "delete", "manage"]
                }
            ],
            "entities": [
                {
                    "name": "user",
                    "fields": {
                        "id": "integer",
                        "email": "string",
                        "name": "string",
                        "role": "string",
                        "created_at": "datetime"
                    },
                    "relations": []
                }
            ],
            "business_rules": [
                "Users must be authenticated",
                "Admin has full access"
            ],
            "assumptions": [
                "Generated from fallback due to extraction failure",
                f"Error: {error_msg}",
                "Basic app structure provided for reliability"
            ]
        }