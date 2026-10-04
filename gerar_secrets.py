import json
import toml
from pathlib import Path

# Nome do teu ficheiro JSON da conta de serviço
JSON_FILE = "gestor-notas-509514-4f5910ef7524.json"

with open(JSON_FILE, "r", encoding="utf-8") as f:
    data = json.load(f)

config = {"gcp_service_account": data}

Path(".streamlit").mkdir(exist_ok=True)
with open(".streamlit/secrets.toml", "w", encoding="utf-8") as f:
    toml.dump(config, f)

print("secrets.toml gerado com sucesso!")