import os
import pytest

os.environ.setdefault(
    "DATABASE_URL", "postgresql://nexus:nexus@localhost:5432/nexusdb_test"
)
os.environ["NEXUS_DISABLE_SCHEDULER"] = "1"
