import json
import glob
from jsonschema import validate

def validate_all():
    schema_path = "../data/strategies/_schema.json"
    try:
        with open(schema_path, "r") as f:
            schema = json.load(f)
    except FileNotFoundError:
        print("Schema not found.")
        return

    files = glob.glob("../data/strategies/*.json")
    for file in files:
        if file.endswith("_schema.json"):
            continue
        try:
            with open(file, "r") as f:
                data = json.load(f)
            validate(instance=data, schema=schema)
            print(f"{file} passed validation.")
        except Exception as e:
            print(f"{file} failed validation: {e}")

if __name__ == "__main__":
    validate_all()
