
"""Base classes for pipeline stages"""
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
import json
import logging
from datetime import datetime
from .config import PipelineConfig

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PipelineStage(ABC):
    """Base class for all pipeline stages"""
    
    def __init__(self, name: str):
        self.name = name
        self.config = PipelineConfig()
        self.metrics = {
            "stage": name,
            "start_time": None,
            "end_time": None,
            "duration": None,
            "success": False,
            "retries": 0,
            "errors": []
        }
    
    @abstractmethod
    def process(self, input_data: Any) -> Any:
        """Process the input data for this stage"""
        pass
    
    def execute(self, input_data: Any) -> Dict[str, Any]:
        """Execute the stage with error handling and metrics"""
        self.metrics["start_time"] = datetime.now()
        
        try:
            logger.info(f"[{self.name}] Starting execution")
            output = self.process(input_data)
            
            self.metrics["success"] = True
            self.metrics["end_time"] = datetime.now()
            self.metrics["duration"] = (
                self.metrics["end_time"] - self.metrics["start_time"]
            ).total_seconds()
            
            duration_str = str(self.metrics.get("duration", 0))
            logger.info(f"[{self.name}] Completed in {duration_str}s")
            return {
                "success": True,
                "output": output,
                "metrics": self.metrics
            }
            
        except Exception as e:
            self.metrics["errors"].append(str(e))
            self.metrics["success"] = False
            self.metrics["end_time"] = datetime.now()
            logger.error(f"[{self.name}] Failed: {str(e)}")
            
            return {
                "success": False,
                "output": None,
                "metrics": self.metrics,
                "error": str(e)
            }
    
    def log_metrics(self):
        """Log stage metrics"""
        logger.info(f"[{self.name}] Metrics: {json.dumps(self.metrics, default=str)}")
