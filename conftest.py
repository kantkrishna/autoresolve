"""
Global Pytest Configuration and Test Collection Guardrails.
Located at the repository root to configure workspace boundaries.
"""

import os
import sys
from pathlib import Path
from unittest.mock import MagicMock

# 1. Inject Mock Environment Variables BEFORE Pytest collects modules.
os.environ["KAFKA_BOOTSTRAP_SERVERS"] = "mock:9092"
os.environ["POSTGRES_DSN"] = "postgresql://user:pass@localhost:5432/db"
os.environ["POSTGRES_URL"] = "postgresql://user:pass@localhost:5432/db"
os.environ["QDRANT_URL"] = "http://localhost:6333"
os.environ["ANTHROPIC_API_KEY"] = "sk-ant-mock-key"

# 2. Align repository paths for cross-folder discovery
root_dir = Path(__file__).parent.absolute()
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

# 3. CRITICAL SURGICAL FIX: Mock out LangGraph's checkpointer parent and child modules.
# This informs the Python import engine that both namespaces exist as valid targets.
sys.modules["langgraph.checkpoint.postgres"] = MagicMock()
sys.modules["langgraph.checkpoint.postgres.aio"] = MagicMock()

# 4. Safely intercept top-level connection factories on the real driver
try:
    import psycopg
    psycopg.connect = MagicMock()
except ImportError:
    pass