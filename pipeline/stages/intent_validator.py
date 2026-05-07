"""Intent Validator - Ensures extracted intents are complete and logical"""
from pipeline.base import PipelineStage
from typing import Dict, Any, List

class IntentValidator(PipelineStage):
    """Validates and enriches extracted intents"""
    
    def __init__(self):
        super().__init__("IntentValidator")
    
    def process(self, intent: Dict[str, Any]) -> Dict[str, Any]:
        """Validate intent completeness and consistency"""
        
        issues = []
        warnings = []
        
        # Check 1: Does the app have a name and type?
        if not intent.get("app_name"):
            issues.append("Missing app_name")
        if not intent.get("app_type"):
            issues.append("Missing app_type")
        
        # Check 2: Are there features?
        if not intent.get("features"):
            warnings.append("No features extracted")
        else:
            # Check each feature
            for feature in intent["features"]:
                if not feature.get("name"):
                    issues.append(f"Feature missing name: {feature}")
                if "description" not in feature:
                    warnings.append(f"Feature missing description: {feature.get('name')}")
        
        # Check 3: Are roles defined?
        if not intent.get("roles"):
            warnings.append("No roles defined, adding default user role")
            intent["roles"] = [{
                "name": "user",
                "permissions": ["read", "write"]
            }]
        
        # Check 4: Do features that require auth have matching roles?
        roles_names = [r["name"] for r in intent.get("roles", [])]
        for feature in intent.get("features", []):
            if feature.get("required_role") and feature["required_role"] not in roles_names:
                warnings.append(f"Feature '{feature['name']}' requires role '{feature['required_role']}' which doesn't exist")
        
        # Check 5: Are entities defined?
        if not intent.get("entities"):
            warnings.append("No entities defined")
            # Add default user entity
            intent["entities"] = [{
                "name": "user",
                "fields": {
                    "id": "integer",
                    "email": "string",
                    "name": "string",
                    "created_at": "datetime"
                },
                "relations": []
            }]
        
        # Check 6: Business rules consistency
        if not intent.get("business_rules"):
            warnings.append("No business rules extracted")
        
        # Check 7: Entity field types are valid
        valid_types = {"string", "integer", "boolean", "datetime", "float", "text", "json"}
        for entity in intent.get("entities", []):
            for field_name, field_type in entity.get("fields", {}).items():
                if field_type.lower() not in valid_types:
                    warnings.append(f"Entity '{entity['name']}' has invalid field type '{field_type}' for '{field_name}'")
        
        # Add validation metadata
        intent["_validation"] = {
            "valid": len(issues) == 0,
            "issues": issues,
            "warnings": warnings,
            "timestamp": self.metrics.get("start_time")
        }
        
        return intent