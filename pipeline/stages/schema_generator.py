"""Stage 3: Schema Generation - Architecture to Detailed Schemas"""
import json
from typing import Dict, Any, List
from pipeline.base import PipelineStage
from pipeline.utils.llm import LLMHelper

class SchemaGenerator(PipelineStage):
    """Generates UI, API, DB, and Auth schemas from architecture"""
    
    def __init__(self):
        super().__init__("SchemaGenerator")
        self.llm = LLMHelper()
    
    def process(self, design: Dict[str, Any]) -> Dict[str, Any]:
        """Generate all schemas from design"""
        
        schemas = {}
        
        # Generate each schema
        schemas["ui"] = self._generate_ui_schema(design)
        schemas["api"] = self._generate_api_schema(design)
        schemas["database"] = self._generate_db_schema(design)
        schemas["auth"] = self._generate_auth_schema(design)
        
        return schemas
    
    def _generate_ui_schema(self, design: Dict[str, Any]) -> Dict[str, Any]:
        """Generate UI configuration"""
        
        pages = design.get("pages", [])
        ui_pages = {}
        
        for page in pages:
            page_name = page.get("name", "Unknown")
            components = page.get("components", [])
            
            # Convert components to structured format
            ui_components = []
            for comp in components:
                ui_components.append({
                    "type": self._map_to_ui_type(comp),
                    "props": {
                        "title": comp,
                        "route": page.get("route", "/")
                    },
                    "events": self._get_component_events(comp)
                })
            
            ui_pages[page_name] = ui_components
        
        return {
            "pages": ui_pages,
            "layouts": {
                "default": {
                    "header": True,
                    "sidebar": True,
                    "footer": False
                },
                "auth": {
                    "header": False,
                    "sidebar": False,
                    "footer": False
                }
            },
            "theme": {
                "primary": "#007bff",
                "secondary": "#6c757d",
                "success": "#28a745",
                "danger": "#dc3545"
            }
        }
    
    def _map_to_ui_type(self, component_name: str) -> str:
        """Map component name to UI type"""
        name = component_name.lower()
        
        if "form" in name:
            return "Form"
        elif "list" in name or "table" in name:
            return "DataTable"
        elif "card" in name:
            return "Card"
        elif "chart" in name:
            return "Chart"
        elif "search" in name:
            return "SearchInput"
        elif "filter" in name:
            return "FilterPanel"
        elif "stats" in name:
            return "StatsGrid"
        elif "history" in name or "activity" in name:
            return "Timeline"
        elif "pricing" in name or "comparison" in name:
            return "PricingTable"
        elif "invoice" in name:
            return "InvoiceList"
        else:
            return "Container"
    
    def _get_component_events(self, component_name: str) -> List[str]:
        """Get relevant events for a component"""
        events = ["onLoad"]
        
        if "form" in component_name.lower():
            events.extend(["onSubmit", "onValidate"])
        if "list" in component_name.lower() or "table" in component_name.lower():
            events.extend(["onRowClick", "onSort", "onFilter"])
        if "search" in component_name.lower():
            events.append("onSearch")
        
        return events
    
    def _generate_api_schema(self, design: Dict[str, Any]) -> Dict[str, Any]:
        """Generate API configuration"""
        
        endpoints = []
        data_flows = design.get("data_flows", [])
        
        # Extract endpoints from data flows
        for flow in data_flows:
            if isinstance(flow, dict):
                target = flow.get("target", "")
                data_fields = flow.get("data", [])
                response_fields = flow.get("response", [])
                
                # Generate CRUD endpoints
                entity_name = target.replace("API", "").lower()
                
                # GET list
                endpoints.append({
                    "method": "GET",
                    "path": f"/{entity_name}",
                    "request_body": None,
                    "response": {field: "string" for field in response_fields},
                    "auth_required": True,
                    "required_role": None
                })
                
                # GET by ID
                endpoints.append({
                    "method": "GET",
                    "path": f"/{entity_name}/:id",
                    "request_body": None,
                    "response": {field: "string" for field in response_fields},
                    "auth_required": True,
                    "required_role": None
                })
                
                # POST create
                endpoints.append({
                    "method": "POST",
                    "path": f"/{entity_name}",
                    "request_body": {field: "string" for field in data_fields if field not in ["id"]},
                    "response": {field: "string" for field in response_fields},
                    "auth_required": True,
                    "required_role": None
                })
                
                # PUT update
                endpoints.append({
                    "method": "PUT",
                    "path": f"/{entity_name}/:id",
                    "request_body": {field: "string" for field in data_fields},
                    "response": {field: "string" for field in response_fields},
                    "auth_required": True,
                    "required_role": None
                })
                
                # DELETE
                endpoints.append({
                    "method": "DELETE",
                    "path": f"/{entity_name}/:id",
                    "request_body": None,
                    "response": {"success": "boolean"},
                    "auth_required": True,
                    "required_role": "admin"
                })
        
        # Add auth endpoints
        endpoints.append({
            "method": "POST",
            "path": "/auth/login",
            "request_body": {"email": "string", "password": "string"},
            "response": {"token": "string", "user": "object"},
            "auth_required": False,
            "required_role": None
        })
        
        endpoints.append({
            "method": "POST",
            "path": "/auth/register",
            "request_body": {"email": "string", "password": "string", "name": "string"},
            "response": {"token": "string", "user": "object"},
            "auth_required": False,
            "required_role": None
        })
        
        # Analytics endpoint (admin only)
        pages = design.get("pages", [])
        for page in pages:
            if isinstance(page, dict) and page.get("required_role") == "admin":
                endpoints.append({
                    "method": "GET",
                    "path": f"{page.get('route', '')}/data",
                    "request_body": None,
                    "response": {"data": "array"},
                    "auth_required": True,
                    "required_role": "admin"
                })
        
        return {
            "endpoints": endpoints,
            "middleware": ["auth", "cors", "rateLimiter"]
        }
    
    def _generate_db_schema(self, design: Dict[str, Any]) -> Dict[str, Any]:
        """Generate database schema"""
        
        tables = {}
        relations = []
        data_flows = design.get("data_flows", [])
        
        # Create users table (always needed)
        tables["users"] = {
            "id": {"type": "integer", "required": True, "unique": True},
            "email": {"type": "string", "required": True, "unique": True},
            "password": {"type": "string", "required": True},
            "name": {"type": "string", "required": True},
            "role": {"type": "string", "required": True, "default": "user"},
            "created_at": {"type": "datetime", "required": True},
            "updated_at": {"type": "datetime", "required": True}
        }
        
        # Extract entities from data flows
        for flow in data_flows:
            if isinstance(flow, dict):
                entity_name = flow.get("target", "").replace("API", "")
                if entity_name and entity_name.lower() != "auth":
                    table_name = entity_name.lower()
                    
                    if table_name not in tables:
                        tables[table_name] = {
                            "id": {"type": "integer", "required": True, "unique": True},
                            "user_id": {"type": "integer", "required": True},
                            "created_at": {"type": "datetime", "required": True},
                            "updated_at": {"type": "datetime", "required": True}
                        }
                        
                        # Add relation to users
                        relations.append({
                            "from": table_name,
                            "to": "users",
                            "type": "belongs_to",
                            "foreign_key": "user_id"
                        })
        
        return {
            "tables": tables,
            "relations": relations
        }
    
    def _generate_auth_schema(self, design: Dict[str, Any]) -> Dict[str, Any]:
        """Generate auth configuration"""
        
        auth_flows = design.get("auth_flows", {})
        pages = design.get("pages", [])
        
        # Extract roles from pages
        roles = set()
        for page in pages:
            if isinstance(page, dict) and page.get("required_role"):
                roles.add(page["required_role"])
        
        if "user" not in roles:
            roles.add("user")
        
        # Generate permissions
        permissions = []
        for role in roles:
            if role == "admin":
                permissions.append({
                    "role": "admin",
                    "resource": "*",
                    "action": "*"
                })
            else:
                permissions.append({
                    "role": role,
                    "resource": f"/{role}s",
                    "action": "read"
                })
                permissions.append({
                    "role": role,
                    "resource": f"/{role}s",
                    "action": "write"
                })
        
        return {
            "roles": list(roles),
            "permissions": permissions,
            "auth_provider": "jwt",
            "session_duration": "24h"
        }