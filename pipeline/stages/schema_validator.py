"""Schema Validator - Cross-checks all schemas for consistency"""
from pipeline.base import PipelineStage
from typing import Dict, Any, List

class SchemaValidator(PipelineStage):
    """Validates schema consistency across layers"""
    
    def __init__(self):
        super().__init__("SchemaValidator")
    
    def process(self, schemas: Dict[str, Any]) -> Dict[str, Any]:
        """Cross-validate all schemas"""
        
        issues = []
        warnings = []
        fixes = []
        
        ui = schemas.get("ui", {})
        api = schemas.get("api", {})
        db = schemas.get("database", {})
        auth = schemas.get("auth", {})
        
        # Check 1: API endpoints have matching DB tables
        api_paths = set()
        for endpoint in api.get("endpoints", []):
            path = endpoint.get("path", "")
            # Extract entity name from path
            parts = path.strip("/").split("/")
            if parts:
                entity = parts[0]
                if entity not in ["auth", "dashboard", "analytics", "settings"]:
                    api_paths.add(entity)
        
        db_tables = set(db.get("tables", {}).keys())
        
        for path in api_paths:
            if path not in db_tables and path != "premium":
                warnings.append(f"API endpoint '/{path}' has no matching DB table")
                fixes.append(f"Consider adding '{path}' table to database")
        
        # Check 2: DB tables have corresponding API endpoints
        for table in db_tables:
            if table not in api_paths and table != "users":
                warnings.append(f"DB table '{table}' has no API endpoint")
        
        # Check 3: UI pages match API endpoints
        ui_pages = list(ui.get("pages", {}).keys())
        api_entities = [p for p in api_paths]
        
        for page in ui_pages:
            page_lower = page.lower()
            # Skip core pages
            if page_lower in ["login", "dashboard", "settings", "analytics"]:
                continue
            
            found = False
            for entity in api_entities:
                if entity in page_lower:
                    found = True
                    break
            
            if not found:
                warnings.append(f"UI page '{page}' has no matching API endpoint")
        
        # Check 4: Auth roles match
        auth_roles = set(auth.get("roles", []))
        
        for endpoint in api.get("endpoints", []):
            required_role = endpoint.get("required_role")
            if required_role and required_role not in auth_roles:
                issues.append(f"API endpoint '{endpoint['path']}' requires role '{required_role}' which doesn't exist in auth config")
                fixes.append(f"Add '{required_role}' to auth roles")
        
        # Check 5: Consistency validation
        if not issues:
            consistency_status = "All schemas are consistent"
        else:
            consistency_status = f"{len(issues)} issues found"
        
        # Add validation metadata
        schemas["_validation"] = {
            "valid": len(issues) == 0,
            "issues": issues,
            "warnings": warnings,
            "fixes": fixes,
            "consistency": consistency_status
        }
        
        return schemas