import inspect
import json
import sys
from pathlib import Path

# Add backend directory to sys.path so we can import src
backend_dir = Path(__file__).parent.parent
sys.path.append(str(backend_dir))

from src.systems.dnd5e import event_types

def generate_markdown(output_file: str):
    """Generates markdown documentation from all Pydantic models in event_types.py."""
    
    inbound_models = []
    outbound_models = []
    
    # Introspect the module to find all Pydantic models
    for name, obj in inspect.getmembers(event_types, inspect.isclass):
        if issubclass(obj, event_types.BaseModel) and obj is not event_types.BaseModel:
            if name.endswith("Payload"):
                outbound_keywords = ["Error", "Advanced", "Damaged", "Healed", "Died", "Added", "Removed", "Started", "Ended", "Rolled", "Pong"]
                is_outbound = any(name.replace("Payload", "").endswith(keyword) for keyword in outbound_keywords)
                if is_outbound:
                    outbound_models.append((name, obj))
                else:
                    inbound_models.append((name, obj))
                    
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("# D&D 5e WebSocket Payloads\n\n")
        f.write("This document was auto-generated from `systems/dnd5e/event_types.py` via `scripts/generate_ws_docs.py`. Do not edit manually.\n\n")
        
        def render_model(name, model):
            schema = model.model_json_schema()
            doc = model.__doc__ or "No description provided."
            event_name = name.replace("Payload", "")
            # Convert CamelCase to snake_case roughly
            event_name = ''.join(['_'+c.lower() if c.isupper() else c for c in event_name]).lstrip('_')
            
            f.write(f"### `{event_name}`\n")
            f.write(f"{doc}\n\n")
            f.write("```json\n")
            
            example = {}
            for prop_name, prop_data in schema.get("properties", {}).items():
                # Provide a better default if possible
                t = prop_data.get("type", "any")
                if t == "string": example[prop_name] = "string"
                elif t == "integer": example[prop_name] = 0
                elif t == "boolean": example[prop_name] = False
                elif t == "array": example[prop_name] = []
                else: example[prop_name] = {}
                
            f.write(json.dumps(example, indent=2) + "\n")
            f.write("```\n\n")

        f.write("## Inbound Events (Client -> Server)\n\n")
        for name, model in sorted(inbound_models, key=lambda x: x[0]):
            render_model(name, model)
            
        f.write("---\n\n")
        f.write("## Outbound Events (Server -> Client)\n\n")
        for name, model in sorted(outbound_models, key=lambda x: x[0]):
            render_model(name, model)

if __name__ == "__main__":
    out_path = Path(__file__).parent.parent.parent / "docs" / "backend" / "reference" / "08_websocket_events_reference.md"
    generate_markdown(str(out_path))
    print(f"Successfully generated {out_path}")
