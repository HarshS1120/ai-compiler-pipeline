"""Stage 4: Repair Engine - Fixes schema inconsistencies"""
from typing import Dict, Any, List
from pipeline.base import PipelineStage

class RepairEngine(PipelineStage):
    """Detects and repairs schema issues automatically"""
    
    def __init__(self):
        super().__init__("RepairEngine")
    
    def process(self, schemas: Dict[str, Any]) -> Dict[str, Any]:
        """Repair inconsistencies in schemas"""
        
        validation = schemas.get("_validation", {})
        warnings = validation.get("warnings", [])
        issues = validation.get("issues", [])
        
        repairs_made = []
        
        # Run all repairs
        schemas, r1 = self._fix_missing_api_endpoints(schemas)
        repairs_made.extend(r1)
        
        schemas, r2 = self._fix_duplicate_tables(schemas)
        repairs_made.extend(r2)
        
        schemas, r3 = self._fix_premium_endpoints(schemas)
        repairs_made.extend(r3)
        
        schemas, r4 = self._fix_auth_consistency(schemas)
        repairs_made.extend(r4)
        
        schemas, r5 = self._fix_missing_db_tables(schemas)
        repairs_made.extend(r5)
        
        schemas, r6 = self._fix_api_db_mismatch(schemas)
        repairs_made.extend(r6)
        
        # Run validation again after repairs
        from pipeline.stages.schema_validator import SchemaValidator
        validator = SchemaValidator()
        schemas = validator.process(schemas)
        
        new_validation = schemas.get("_validation", {})
        
        # Add repair metadata
        schemas["_repairs"] = {
            "repairs_made": len(repairs_made),
            "details": repairs_made,
            "original_warnings": len(warnings),
            "remaining_warnings": len(new_validation.get("warnings", [])),
            "original_issues": len(issues),
            "remaining_issues": len(new_validation.get("issues", []))
        }
        
        return schemas
    
    def _fix_missing_api_endpoints(self, schemas: Dict) -> tuple:
        """Add missing API endpoints for UI pages"""
        repairs = []
        api = schemas.get("api", {})
        ui = schemas.get("ui", {})
    
        ui_pages = list(ui.get("pages", {}).keys())
        existing_endpoints = [ep.get("path", "") for ep in api.get("endpoints", [])]
        existing_paths_flat = []
        for ep in existing_endpoints:
            # Store both full path and first segment
            existing_paths_flat.append(ep)
            existing_paths_flat.append(ep.strip("/").split("/")[0])
        
        # Map page names to endpoints
        page_to_endpoint = {
            "Premium": "/premium",
            "Payments": "/payments",
            "Analytics": "/analytics"
        }
        
        for page_name, endpoint_path in page_to_endpoint.items():
            if page_name in ui_pages:
                # Check if any endpoint starts with this path
                has_endpoint = any(
                    ep == endpoint_path or ep.startswith(endpoint_path + "/") or ep.startswith(endpoint_path.strip("/"))
                    for ep in existing_endpoints
                )
                
                if not has_endpoint:
                    role = "admin" if page_name == "Analytics" else None
                    
                    # For analytics, add both overview and data endpoints
                    if page_name == "Analytics":
                        api["endpoints"].append({
                            "method": "GET",
                            "path": "/analytics/overview",
                            "request_body": None,
                            "response": {"stats": "object"},
                            "auth_required": True,
                            "required_role": "admin"
                        })
                        repairs.append("Added GET /analytics/overview for Analytics page (admin only)")
                    else:
                        api["endpoints"].append({
                            "method": "GET",
                            "path": endpoint_path,
                            "request_body": None,
                            "response": {"data": "array"},
                            "auth_required": True,
                            "required_role": role
                        })
                        repairs.append(f"Added GET {endpoint_path} endpoint for {page_name} page")
        
        schemas["api"] = api
        return schemas, repairs
        
    def _fix_duplicate_tables(self, schemas: Dict) -> tuple:
        """Fix duplicate database tables"""
        repairs = []
        db = schemas.get("database", {})
        tables = db.get("tables", {})
        
        # Merge 'user' into 'users' if both exist
        if "user" in tables and "users" in tables:
            for key, value in tables["user"].items():
                if key not in tables["users"]:
                    tables["users"][key] = value
            del tables["user"]
            repairs.append("Merged duplicate 'user' table into 'users'")
            
            # Update relations
            relations = db.get("relations", [])
            db["relations"] = [r for r in relations if r.get("from") != "user"]
        
        # Fix singular/plural consistency
        if "subscription" in tables and "subscriptions" not in tables:
            tables["subscriptions"] = tables.pop("subscription")
            repairs.append("Renamed 'subscription' to 'subscriptions' for consistency")
        
        schemas["database"] = db
        return schemas, repairs
    
    def _fix_premium_endpoints(self, schemas: Dict) -> tuple:
        """Add premium/subscription related endpoints"""
        repairs = []
        api = schemas.get("api", {})
        db = schemas.get("database", {})
        
        existing_paths = [ep.get("path") for ep in api.get("endpoints", [])]
        
        # Check if premium features are mentioned
        has_premium = any("premium" in path for path in existing_paths)
        
        if has_premium:
            # Add premium plans endpoint
            if "/premium/plans" not in existing_paths:
                api["endpoints"].append({
                    "method": "GET",
                    "path": "/premium/plans",
                    "request_body": None,
                    "response": {"plans": "array"},
                    "auth_required": True,
                    "required_role": None
                })
                repairs.append("Added GET /premium/plans endpoint")
            
            # Add subscription endpoint
            if "/premium/subscribe" not in existing_paths:
                api["endpoints"].append({
                    "method": "POST",
                    "path": "/premium/subscribe",
                    "request_body": {"plan_id": "integer", "payment_method": "string"},
                    "response": {"subscription": "object"},
                    "auth_required": True,
                    "required_role": None
                })
                repairs.append("Added POST /premium/subscribe endpoint")
            
            # Add subscriptions table if missing
            tables = db.get("tables", {})
            if "subscriptions" not in tables:
                tables["subscriptions"] = {
                    "id": {"type": "integer", "required": True, "unique": True},
                    "user_id": {"type": "integer", "required": True},
                    "plan_type": {"type": "string", "required": True},
                    "status": {"type": "string", "required": True, "default": "active"},
                    "start_date": {"type": "datetime", "required": True},
                    "end_date": {"type": "datetime", "required": True}
                }
                db["relations"].append({
                    "from": "subscriptions",
                    "to": "users",
                    "type": "belongs_to",
                    "foreign_key": "user_id"
                })
                repairs.append("Added 'subscriptions' table for premium feature")
        
        schemas["api"] = api
        schemas["database"] = db
        return schemas, repairs
    
    def _fix_auth_consistency(self, schemas: Dict) -> tuple:
        """Ensure auth permissions cover all endpoints"""
        repairs = []
        auth = schemas.get("auth", {})
        permissions = auth.get("permissions", [])
        roles = auth.get("roles", [])
        
        # Ensure user role exists
        if "user" not in roles:
            roles.append("user")
            repairs.append("Added 'user' role")
        
        # Ensure user has basic permissions
        user_perms = [p for p in permissions if p.get("role") == "user"]
        if not user_perms:
            auth["permissions"].append({
                "role": "user",
                "resource": "*",
                "action": "read"
            })
            auth["permissions"].append({
                "role": "user",
                "resource": "*",
                "action": "write"
            })
            repairs.append("Added default permissions for user role")
        
        schemas["auth"] = auth
        return schemas, repairs
    
    def _fix_missing_db_tables(self, schemas: Dict) -> tuple:
        """Add DB tables for API endpoints that lack them"""
        repairs = []
        api = schemas.get("api", {})
        db = schemas.get("database", {})
        tables = db.get("tables", {})
        
        # Extract entities from API paths
        api_entities = set()
        for ep in api.get("endpoints", []):
            path = ep.get("path", "").strip("/")
            parts = path.split("/")
            if parts and parts[0] not in ["auth", "premium"]:
                api_entities.add(parts[0])
        
        # Add missing tables
        for entity in api_entities:
            if entity not in tables and entity not in ["auth", "settings", "dashboard", "analytics"]:
                tables[entity] = {
                    "id": {"type": "integer", "required": True, "unique": True},
                    "user_id": {"type": "integer", "required": True},
                    "created_at": {"type": "datetime", "required": True},
                    "updated_at": {"type": "datetime", "required": True}
                }
                db["relations"].append({
                    "from": entity,
                    "to": "users",
                    "type": "belongs_to",
                    "foreign_key": "user_id"
                })
                repairs.append(f"Added '{entity}' table for API endpoint")
        
        schemas["database"] = db
        return schemas, repairs
    
    def _fix_api_db_mismatch(self, schemas: Dict) -> tuple:
        """Fix mismatches between API endpoints and DB tables"""
        repairs = []
        api = schemas.get("api", {})
        db = schemas.get("database", {})
        tables = db.get("tables", {})
        endpoints = api.get("endpoints", [])
        
        existing_paths = [ep.get("path", "").strip("/").split("/")[0] for ep in endpoints]
        
        # Check DB tables that need API endpoints
        for table_name in tables:
            if table_name not in existing_paths:
                # Add CRUD endpoints for this table
                endpoints.append({
                    "method": "GET",
                    "path": f"/{table_name}",
                    "request_body": None,
                    "response": {"data": "array"},
                    "auth_required": True,
                    "required_role": None
                })
                endpoints.append({
                    "method": "POST",
                    "path": f"/{table_name}",
                    "request_body": {"data": "object"},
                    "response": {"data": "object"},
                    "auth_required": True,
                    "required_role": None
                })
                repairs.append(f"Added API endpoints for '{table_name}' table")
        
        schemas["api"]["endpoints"] = endpoints
        return schemas, repairs