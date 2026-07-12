import os
import sys
from pathlib import Path

# 1. Inject Mock Environment Variables BEFORE Pytest collects modules.
# This prevents Pydantic from crashing when config.py is globally imported.
os.environ["KAFKA_BOOTSTRAP_SERVERS"] = "mock:9092"
os.environ["POSTGRES_DSN"] = "postgresql://user:pass@localhost:5432/db"
os.environ["QDRANT_URL"] = "http://localhost:6333"
os.environ["ANTHROPIC_API_KEY"] = "sk-ant-mock-key"

# 2. Force the repository root into Python's path
root_dir = Path(__file__).parent.absolute()
sys.path.insert(0, str(root_dir))
