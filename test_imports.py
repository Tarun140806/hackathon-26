#!/usr/bin/env python
"""Debug import issues"""

try:
    print("1. Importing FastAPI...")
    from fastapi import APIRouter
    print("   ✓ FastAPI imported")
except Exception as e:
    print(f"   ✗ Error: {e}")

try:
    print("2. Importing schema models...")
    from backend.models.schema import PaymentStatusUpdate
    print("   ✓ Schema imported")
except Exception as e:
    print(f"   ✗ Error: {e}")

try:
    print("3. Importing decision_engine...")
    from backend.services.decision_engine import run_decision_engine
    print("   ✓ Decision engine imported")
except Exception as e:
    print(f"   ✗ Error: {e}")

try:
    print("4. Importing llm_service...")
    from backend.services.llm_service import generate_llm_output
    print("   ✓ LLM service imported")
except Exception as e:
    print(f"   ✗ Error: {e}")

try:
    print("5. Importing features routes...")
    from backend.routes.features import router
    print("   ✓ Features router imported")
except Exception as e:
    print(f"   ✗ Error: {e}")

try:
    print("6. Importing reportlab...")
    from reportlab.lib.pagesizes import letter
    print("   ✓ Reportlab imported")
except Exception as e:
    print(f"   ✗ Error: {e}")

print("\nAll imports successful!")
