"""Complete pipeline runner - orchestrates all stages"""
from typing import Dict, Any
from pipeline.stages.intent_extractor import IntentExtractor
from pipeline.stages.system_designer import SystemDesigner
from pipeline.stages.schema_generator import SchemaGenerator
from pipeline.stages.schema_validator import SchemaValidator
from pipeline.stages.repair_engine import RepairEngine
from pipeline.utils.helpers import safe_json_dumps

class PipelineRunner:
    """Runs the complete compiler pipeline"""
    
    def __init__(self):
        self.extractor = IntentExtractor()
        self.designer = SystemDesigner()
        self.generator = SchemaGenerator()
        self.validator = SchemaValidator()
        self.repair = RepairEngine()
    
    def run(self, prompt: str) -> Dict[str, Any]:
        """Execute the full pipeline"""
        
        execution_log = []
        total_start = __import__('datetime').datetime.now()
        
        # Stage 1: Intent Extraction
        execution_log.append({"stage": "Intent Extraction", "status": "running"})
        intent_result = self.extractor.execute(prompt)
        
        if not intent_result["success"]:
            return {
                "success": False,
                "error": "Intent extraction failed",
                "log": execution_log
            }
        
        intent = intent_result["output"]
        execution_log[-1]["status"] = "completed"
        execution_log[-1]["duration"] = intent_result["metrics"]["duration"]
        
        # Stage 2: System Design
        execution_log.append({"stage": "System Design", "status": "running"})
        design_result = self.designer.execute(intent)
        
        if not design_result["success"]:
            return {
                "success": False,
                "error": "System design failed",
                "log": execution_log
            }
        
        design = design_result["output"]
        execution_log[-1]["status"] = "completed"
        execution_log[-1]["duration"] = design_result["metrics"]["duration"]
        
        # Stage 3: Schema Generation
        execution_log.append({"stage": "Schema Generation", "status": "running"})
        schema_result = self.generator.execute(design)
        
        if not schema_result["success"]:
            return {
                "success": False,
                "error": "Schema generation failed",
                "log": execution_log
            }
        
        schemas = schema_result["output"]
        execution_log[-1]["status"] = "completed"
        execution_log[-1]["duration"] = schema_result["metrics"]["duration"]
        
        # Stage 4: Validation
        execution_log.append({"stage": "Validation", "status": "running"})
        validation_result = self.validator.execute(schemas)
        schemas = validation_result["output"]
        validation_before = schemas.get("_validation", {})
        execution_log[-1]["status"] = "completed"
        execution_log[-1]["warnings"] = len(validation_before.get("warnings", []))
        
        # Stage 5: Repair
        execution_log.append({"stage": "Repair", "status": "running"})
        repair_result = self.repair.execute(schemas)
        schemas = repair_result["output"]
        repairs = schemas.get("_repairs", {})
        execution_log[-1]["status"] = "completed"
        execution_log[-1]["repairs"] = repairs.get("repairs_made", 0)
        
        # Final validation
        final_validation = self.validator.execute(schemas)
        schemas = final_validation["output"]
        final_val = schemas.get("_validation", {})
        
        total_end = __import__('datetime').datetime.now()
        total_duration = (total_end - total_start).total_seconds()
        
        return {
            "success": True,
            "output": schemas,
            "metadata": {
                "total_duration": total_duration,
                "stages": execution_log,
                "final_warnings": final_val.get("warnings", []),
                "final_issues": final_val.get("issues", []),
                "repairs_made": repairs.get("repairs_made", 0)
            }
        }