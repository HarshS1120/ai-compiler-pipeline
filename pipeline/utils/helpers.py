"""Helper utilities for the pipeline"""
import json
from datetime import datetime
from typing import Any

def safe_json_dumps(obj: Any, indent: int = 2) -> str:
    """JSON dumps that handles datetime and other special types"""
    def serializer(o):
        if isinstance(o, datetime):
            return o.isoformat()
        try:
            return str(o)
        except:
            return f"<{type(o).__name__}>"
    
    return json.dumps(obj, indent=indent, default=serializer)

def print_safe_json(obj: Any, title: str = "JSON Output"):
    """Print JSON safely"""
    print(f"\n📄 {title}:")
    print(safe_json_dumps(obj))