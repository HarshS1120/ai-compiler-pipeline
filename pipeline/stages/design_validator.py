"""Design Validator - Ensures architecture is complete and consistent"""
from pipeline.base import PipelineStage
from typing import Dict, Any

class DesignValidator(PipelineStage):
    """Validates the system design"""
    
    def __init__(self):
        super().__init__("DesignValidator")
    
    def process(self, design: Dict[str, Any]) -> Dict[str, Any]:
        """Validate design completeness"""
        
        issues = []
        warnings = []
        
        # Check pages
        pages = design.get("pages", [])
        if not pages:
            issues.append("No pages defined")
        else:
            # Check each page has required fields
            for page in pages:
                if not page.get("name"):
                    issues.append(f"Page missing name")
                if not page.get("route"):
                    issues.append(f"Page '{page.get('name')}' missing route")
                if not page.get("components"):
                    warnings.append(f"Page '{page.get('name')}' has no components")
                
                # Check route format
                route = page.get("route", "")
                if route and not route.startswith("/"):
                    warnings.append(f"Page '{page.get('name')}' route doesn't start with '/'")
            
            # Check for duplicate routes
            routes = [p.get("route") for p in pages]
            duplicates = [r for r in routes if routes.count(r) > 1]
            if duplicates:
                issues.append(f"Duplicate routes found: {list(set(duplicates))}")
        
        # Check data flows
        data_flows = design.get("data_flows", [])
        if not data_flows:
            warnings.append("No data flows defined")
        
        # Check auth flows
        auth_flows = design.get("auth_flows", {})
        if not auth_flows:
            warnings.append("No auth flows defined")
        else:
            if "login_flow" not in auth_flows:
                issues.append("Missing login_flow in auth_flows")
        
        # Add validation metadata
        design["_validation"] = {
            "valid": len(issues) == 0,
            "issues": issues,
            "warnings": warnings
        }
        
        return design