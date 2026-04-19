import json
import os
import uuid

IDENTITY_FILE = "identity.json"

def load_or_create_identity():

    # If identity already exists → load it
    if os.path.exists(IDENTITY_FILE):
        try:
            with open(IDENTITY_FILE, "r") as f:
                return json.load(f)
        except:
            pass

    # Otherwise create new one
    identity = {
        "node_id": f"node-{uuid.uuid4().hex[:8]}",
        "member_id": None,
        "created_ts": int(__import__("time").time())
    }

    with open(IDENTITY_FILE, "w") as f:
        json.dump(identity, f, indent=2)

    return identity