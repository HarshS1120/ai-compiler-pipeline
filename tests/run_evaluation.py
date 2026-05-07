"""Evaluation Framework - Tests pipeline against dataset"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import time
from datetime import datetime
from pipeline.runner import PipelineRunner

def load_test_data():
    """Load test prompts from JSON file"""
    data_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                             "data", "test_prompts.json")
    
    with open(data_path, 'r') as f:
        return json.load(f)

def evaluate_prompt(runner, test_case, category):
    """Evaluate a single test case"""
    
    prompt = test_case["prompt"]
    test_id = test_case["id"]
    
    start_time = time.time()
    
    try:
        result = runner.run(prompt)
        duration = time.time() - start_time
        
        if not result.get("success"):
            return {
                "id": test_id,
                "category": category,
                "prompt": prompt[:100] + "...",
                "success": False,
                "error": result.get("error", "Unknown error"),
                "duration": duration
            }
        
        output = result["output"]
        metadata = result["metadata"]
        
        # Count generated items
        api_endpoints = len(output.get("api", {}).get("endpoints", []))
        db_tables = len(output.get("database", {}).get("tables", {}))
        ui_pages = len(output.get("ui", {}).get("pages", {}))
        auth_roles = len(output.get("auth", {}).get("roles", []))
        repairs = output.get("_repairs", {}).get("repairs_made", 0)
        final_warnings = len(metadata.get("final_warnings", []))
        
        # Check feature detection (for real world prompts)
        feature_score = None
        if "expected_features" in test_case:
            detected_features = []
            for stage in metadata.get("stages", []):
                if stage["stage"] == "Intent Extraction":
                    # Check the output for features
                    pass
            
            # Count how many expected features are detected
            # This is approximate since features are in structured format
            output_str = json.dumps(output).lower()
            expected = test_case.get("expected_features", [])
            found = sum(1 for f in expected if f.lower() in output_str)
            feature_score = f"{found}/{len(expected)}"
        
        return {
            "id": test_id,
            "category": category,
            "type": test_case.get("type", "normal"),
            "prompt": prompt[:100] + "...",
            "success": True,
            "duration": round(duration, 2),
            "api_endpoints": api_endpoints,
            "db_tables": db_tables,
            "ui_pages": ui_pages,
            "auth_roles": auth_roles,
            "repairs": repairs,
            "warnings": final_warnings,
            "feature_detection": feature_score,
            "assumptions": len(output.get("ui", {}).get("pages", {}))  # Proxy for output quality
        }
        
    except Exception as e:
        duration = time.time() - start_time
        return {
            "id": test_id,
            "category": category,
            "prompt": prompt[:100] + "...",
            "success": False,
            "error": str(e),
            "duration": round(duration, 2)
        }

def run_full_evaluation():
    """Run complete evaluation suite"""
    
    print("\n" + "="*70)
    print("📊 AI COMPILER PIPELINE - EVALUATION FRAMEWORK")
    print("="*70)
    
    # Load test data
    data = load_test_data()
    real_prompts = data.get("real_world_prompts", [])
    edge_cases = data.get("edge_cases", [])
    
    print(f"\n📁 Test Dataset:")
    print(f"   Real-world prompts: {len(real_prompts)}")
    print(f"   Edge cases: {len(edge_cases)}")
    print(f"   Total: {len(real_prompts) + len(edge_cases)}")
    
    # Initialize runner
    runner = PipelineRunner()
    
    results = {
        "real_world": [],
        "edge_cases": []
    }
    
    # Test real-world prompts
    print("\n" + "-"*70)
    print("🎯 TESTING REAL-WORLD PROMPTS")
    print("-"*70)
    
    for i, test in enumerate(real_prompts, 1):
        print(f"\n[{i}/{len(real_prompts)}] {test['id']}: {test['prompt'][:80]}...")
        result = evaluate_prompt(runner, test, "real_world")
        results["real_world"].append(result)
        
        if result["success"]:
            print(f"   ✅ Success | ⏱️ {result['duration']}s | 🔌 {result['api_endpoints']} endpoints | 🗄️ {result['db_tables']} tables")
        else:
            print(f"   ❌ Failed: {result.get('error', 'Unknown')}")
    
    # Test edge cases
    print("\n" + "-"*70)
    print("🔪 TESTING EDGE CASES")
    print("-"*70)
    
    for i, test in enumerate(edge_cases, 1):
        print(f"\n[{i}/{len(edge_cases)}] {test['id']} ({test['type']}): {test['prompt'][:80]}...")
        result = evaluate_prompt(runner, test, "edge_case")
        results["edge_cases"].append(result)
        
        if result["success"]:
            print(f"   ✅ Handled | ⏱️ {result['duration']}s | 🔧 {result['repairs']} repairs | ⚠️ {result['warnings']} warnings")
        else:
            print(f"   ❌ Failed: {result.get('error', 'Unknown')}")
    
    # Calculate metrics
    print("\n" + "="*70)
    print("📈 EVALUATION METRICS")
    print("="*70)
    
    all_results = results["real_world"] + results["edge_cases"]
    successful = [r for r in all_results if r["success"]]
    failed = [r for r in all_results if not r["success"]]
    
    if successful:
        durations = [r["duration"] for r in successful]
        repairs = [r.get("repairs", 0) for r in successful]
        warnings = [r.get("warnings", 0) for r in successful]
        
        print(f"\n🎯 Success Rate: {len(successful)}/{len(all_results)} ({len(successful)/len(all_results)*100:.0f}%)")
        print(f"\n⏱️  Latency:")
        print(f"   Average: {sum(durations)/len(durations):.2f}s")
        print(f"   Min: {min(durations):.2f}s")
        print(f"   Max: {max(durations):.2f}s")
        print(f"\n🔧 Repairs:")
        print(f"   Average: {sum(repairs)/len(repairs):.1f} per request")
        print(f"   Total repairs: {sum(repairs)}")
        print(f"\n⚠️  Warnings:")
        print(f"   Average: {sum(warnings)/len(warnings):.1f} per request")
        print(f"   Zero-warning rate: {sum(1 for w in warnings if w == 0)}/{len(warnings)} ({sum(1 for w in warnings if w == 0)/len(warnings)*100:.0f}%)")
    
    if failed:
        print(f"\n❌ Failures:")
        failure_types = {}
        for f in failed:
            error_type = f.get("type", "unknown")
            failure_types[error_type] = failure_types.get(error_type, 0) + 1
        
        for ftype, count in failure_types.items():
            print(f"   {ftype}: {count}")
        for f in failed:
            print(f"   - {f['id']}: {f.get('error', 'Unknown')[:100]}")
    
    # Category breakdown
    print(f"\n📊 By Category:")
    for category in ["real_world", "edge_case"]:
        cat_results = [r for r in all_results if r.get("category") == category]
        cat_success = [r for r in cat_results if r["success"]]
        if cat_results:
            print(f"   {category}: {len(cat_success)}/{len(cat_results)} ({len(cat_success)/len(cat_results)*100:.0f}%)")
    
    # Save results
    output_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                               "data", "evaluation_results.json")
    
    timestamp = datetime.now().isoformat()
    with open(output_path, 'w') as f:
        json.dump({
            "timestamp": timestamp,
            "results": results,
            "summary": {
                "total": len(all_results),
                "success": len(successful),
                "failed": len(failed),
                "success_rate": f"{len(successful)/len(all_results)*100:.0f}%",
                "avg_duration": f"{sum(durations)/len(durations):.2f}s" if successful else "N/A",
                "avg_repairs": f"{sum(repairs)/len(repairs):.1f}" if successful and repairs else "N/A"
            }
        }, f, indent=2)
    
    print(f"\n💾 Results saved to: data/evaluation_results.json")
    
    return results

if __name__ == "__main__":
    run_full_evaluation()
    print("\n✅ Evaluation complete!")