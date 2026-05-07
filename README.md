# AI Compiler Pipeline

A multi-stage compiler-like system that converts natural language into production-ready application configurations.

## 🏗️ Architecture

User Input → Intent Extractor → System Designer → Schema Generator → Validator → Repair Engine → Output JSON


## 🚀 Quick Start

1. Clone and install:
```bash
pip install -r requirements.txt

2. Add Groq API key to .env:
GROQ_API_KEY=your_key_here
GROQ_MODEL=llama-3.1-8b-instant
LOG_LEVEL=INFO

3. Run the web interface:
cd web/api
python -m uvicorn main:app --reload --port 8000

4. Open http://localhost:8000/app

📊 Pipeline Stages
Intent Extraction - Parses NL → Structured intent (features, roles, entities)

System Design - Intent → Architecture (pages, data flows, auth)

Schema Generation - Architecture → UI/API/DB/Auth schemas

Validation - Cross-layer consistency checks

Repair Engine - Auto-fixes inconsistencies

🎯 Features
Multi-stage pipeline (not single prompt)

Strict JSON schema enforcement

Cross-layer validation

Automatic repair engine

Deterministic behavior

Execution-aware output

📈 Metrics
Typical latency: 2-10s

Success rate: 100% on test prompts

Auto-repairs: 3-10 per generation


Final test run
python test_frontend.py
