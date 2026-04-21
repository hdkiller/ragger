import json
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from ragger.server.app import app


if __name__ == "__main__":
    output_path = PROJECT_ROOT / "openapi.json"
    output_path.write_text(json.dumps(app.openapi(), indent=2))
    print(f"Wrote OpenAPI spec to {output_path}")
