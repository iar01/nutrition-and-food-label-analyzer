import json
from pathlib import Path

from labellens.api.app import create_app

app = create_app()  # building the app does not load any models, so this is instant
Path("docs").mkdir(exist_ok=True)
Path("docs/openapi.json").write_text(json.dumps(app.openapi(), indent=2), encoding="utf-8")
print("wrote docs/openapi.json with", len(app.openapi()["paths"]), "paths")
