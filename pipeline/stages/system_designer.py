"""Stage 2: System Design Layer - Intent to Architecture"""
import json
from typing import Dict, Any, List
from pipeline.base import PipelineStage
from pipeline.utils.llm import LLMHelper

class SystemDesigner(PipelineStage):
    """Converts structured intent into application architecture"""
    
    def __init__(self):
        super().__init__("SystemDesigner")
        self.llm = LLMHelper()
    
    def process(self, intent: Dict[str, Any]) -> Dict[str, Any]:
        """Design system architecture from intent"""
        
        try:
            # First, do rule-based architecture planning
            architecture = self._plan_architecture(intent)
            
            # Then, use LLM to enhance the design
            enhanced = self._enhance_with_llm(intent, architecture)
            
            return enhanced
            
        except Exception as e:
            # Return basic architecture if enhancement fails
            print(f"⚠️  Enhancement failed: {e}, using basic architecture")
            return self._plan_architecture(intent)
    
    def _plan_architecture(self, intent: Dict[str, Any]) -> Dict[str, Any]:
        """Rule-based architecture planning"""
        
        features = intent.get("features", [])
        entities = intent.get("entities", [])
        
        # Safely extract feature names
        feature_names = []
        for f in features:
            if isinstance(f, dict):
                feature_names.append(f.get("name", "").lower())
            elif isinstance(f, str):
                feature_names.append(f.lower())
        
        # Generate pages based on features
        pages = []
        
        # Always add these core pages
        pages.append({
            "name": "Login",
            "route": "/login",
            "components": ["LoginForm"],
            "required_role": None,
            "api_calls": ["POST /auth/login"]
        })
        
        pages.append({
            "name": "Dashboard",
            "route": "/dashboard",
            "components": ["StatsCards", "RecentActivity", "QuickActions"],
            "required_role": None,
            "api_calls": ["GET /dashboard/stats"]
        })
        
        # Feature-specific pages
        page_mappings = {
            "contacts": {
                "name": "Contacts",
                "route": "/contacts",
                "components": ["ContactsList", "ContactCard", "ContactForm", "SearchBar"],
                "api_calls": ["GET /contacts", "POST /contacts", "PUT /contacts/:id", "DELETE /contacts/:id"]
            },
            "premium": {
                "name": "Premium",
                "route": "/premium",
                "components": ["PricingTable", "PaymentForm", "FeatureComparison"],
                "api_calls": ["GET /premium/plans", "POST /premium/subscribe"]
            },
            "payments": {
                "name": "Payments",
                "route": "/payments",
                "components": ["PaymentHistory", "InvoiceList", "PaymentMethod"],
                "api_calls": ["GET /payments", "POST /payments", "GET /payments/:id"]
            },
            "analytics": {
                "name": "Analytics",
                "route": "/analytics",
                "components": ["Charts", "Reports", "DataTable", "Filters"],
                "required_role": "admin",
                "api_calls": ["GET /analytics/overview", "GET /analytics/reports"]
            }
        }
        
        # Add feature-specific pages
        for feature_name in feature_names:
            for key, page in page_mappings.items():
                if key in feature_name and page["name"] not in [p["name"] for p in pages]:
                    pages.append(page.copy())
        
        # Add settings page
        pages.append({
            "name": "Settings",
            "route": "/settings",
            "components": ["UserProfile", "Preferences", "SecuritySettings"],
            "required_role": None,
            "api_calls": ["GET /settings", "PUT /settings"]
        })
        
        # Define data flows
        data_flows = []
        
        # Authentication flow
        data_flows.append({
            "name": "Authentication",
            "source": "LoginForm",
            "target": "AuthAPI",
            "data": ["email", "password"],
            "response": ["token", "user"]
        })
        
        # CRUD flows for each entity
        for entity in entities:
            if isinstance(entity, dict):
                entity_name = entity.get("name", "")
                fields = entity.get("fields", {})
                if entity_name:
                    data_flows.append({
                        "name": f"{entity_name.capitalize()}CRUD",
                        "source": f"{entity_name.capitalize()}Form",
                        "target": f"{entity_name.capitalize()}API",
                        "data": list(fields.keys()) if fields else ["data"],
                        "response": [f"{entity_name}_data"]
                    })
        
        # Authorization flows
        auth_flows = {
            "login_flow": {
                "steps": [
                    "User enters credentials",
                    "System validates against database",
                    "JWT token generated",
                    "Token stored in browser",
                    "User redirected to dashboard"
                ]
            },
            "role_check": {
                "steps": [
                    "Request received with JWT token",
                    "Token decoded to get user role",
                    "Role checked against required permissions",
                    "Access granted or denied"
                ]
            },
            "premium_gating": {
                "steps": [
                    "User requests premium feature",
                    "System checks subscription status",
                    "If premium: allow access",
                    "If not: redirect to premium page"
                ]
            }
        }
        
        return {
            "pages": pages,
            "data_flows": data_flows,
            "auth_flows": auth_flows
        }
    
    def _enhance_with_llm(self, intent: Dict[str, Any], architecture: Dict[str, Any]) -> Dict[str, Any]:
        """Use LLM to enhance and validate the architecture"""
        
        # Safely extract data for prompts
        features_names = []
        for f in intent.get("features", []):
            if isinstance(f, dict):
                features_names.append(f.get("name", str(f)))
            else:
                features_names.append(str(f))
        
        roles_names = []
        for r in intent.get("roles", []):
            if isinstance(r, dict):
                roles_names.append(r.get("name", str(r)))
            else:
                roles_names.append(str(r))
        
        entities_names = []
        for e in intent.get("entities", []):
            if isinstance(e, dict):
                entities_names.append(e.get("name", str(e)))
            else:
                entities_names.append(str(e))
        
        pages_names = []
        for p in architecture.get("pages", []):
            if isinstance(p, dict):
                pages_names.append(p.get("name", str(p)))
            else:
                pages_names.append(str(p))
        
        flows_names = []
        for f in architecture.get("data_flows", []):
            if isinstance(f, dict):
                flows_names.append(f.get("name", str(f)))
            else:
                flows_names.append(str(f))
        
        try:
            system_prompt = """You are a senior software architect. Review the proposed architecture.

Output ONLY valid JSON:
{
  "pages": [],
  "data_flows": [],
  "additions": [],
  "concerns": []
}"""
            
            user_prompt = f"""Review this architecture:

FEATURES: {json.dumps(features_names)}
ROLES: {json.dumps(roles_names)}
ENTITIES: {json.dumps(entities_names)}

CURRENT PAGES: {json.dumps(pages_names)}
CURRENT DATA FLOWS: {json.dumps(flows_names)}

Add any missing pages or data flows. Identify concerns."""
            
            result = self.llm.complete_with_retry(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.2,
                max_tokens=2000
            )
            
            # Merge LLM suggestions
            if result and "error" not in result:
                for page in result.get("pages", []):
                    if isinstance(page, dict) and page.get("name") not in [p.get("name") for p in architecture["pages"] if isinstance(p, dict)]:
                        architecture["pages"].append(page)
                
                for flow in result.get("data_flows", []):
                    if isinstance(flow, dict) and flow.get("name") not in [f.get("name") for f in architecture["data_flows"] if isinstance(f, dict)]:
                        architecture["data_flows"].append(flow)
                
                architecture["_llm_additions"] = result.get("additions", [])
                architecture["_llm_concerns"] = result.get("concerns", [])
        
        except Exception as e:
            print(f"⚠️  LLM enhancement skipped: {e}")
        
        return architecture