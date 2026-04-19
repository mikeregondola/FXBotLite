import json
import os
import uuid


class NodeManager:

    def __init__(self, file_path="nodes.json"):
        self.file_path = file_path
        self.nodes = {}
        self._load_nodes()

    # --------------------------------------------------
    # LOAD
    # --------------------------------------------------
    def _load_nodes(self):

        if not os.path.exists(self.file_path):
            print("[NODE] No nodes.json found")
            self.nodes = {}
            return

        try:
            with open(self.file_path, "r") as f:
                self.nodes = json.load(f)
            print(f"[NODE] Loaded {len(self.nodes)} nodes")

        except Exception as e:
            print(f"[NODE ERROR] Load failed: {e}")
            self.nodes = {}

    # --------------------------------------------------
    # SAVE
    # --------------------------------------------------
    def _save_nodes(self):

        try:
            with open(self.file_path, "w") as f:
                json.dump(self.nodes, f, indent=4)
            print("[NODE] Saved nodes.json")

        except Exception as e:
            print(f"[NODE ERROR] Save failed: {e}")

    # --------------------------------------------------
    # REGISTER
    # --------------------------------------------------
    def register_node(self, telegram_id):

        print(f"[NODE] Register request from {telegram_id}")

        for node_id, node in self.nodes.items():
            if node["telegram_id"] == telegram_id:
                return node_id, node["api_key"]

        node_id = f"NODE_{uuid.uuid4().hex[:8]}"
        api_key = uuid.uuid4().hex

        self.nodes[node_id] = {
            "telegram_id": telegram_id,
            "api_key": api_key,
            "tier": "FREE",
            "enabled": True
        }

        self._save_nodes()

        return node_id, api_key

    # --------------------------------------------------
    # CHECK REGISTERED
    # --------------------------------------------------
    def is_registered(self, telegram_id):

        return any(
            node["telegram_id"] == telegram_id
            for node in self.nodes.values()
        )

    # --------------------------------------------------
    # GET CHAT ID
    # --------------------------------------------------
    def get_chat_id(self, node_id):

        node = self.nodes.get(node_id)
        if node:
            return node.get("telegram_id")
        return None

    # --------------------------------------------------
    # VALIDATE
    # --------------------------------------------------
    def validate(self, node_id, api_key):

        node = self.nodes.get(node_id)

        if not node:
            return False, "Node not found"

        if node["api_key"] != api_key:
            return False, "Invalid API key"

        if not node.get("enabled", True):
            return False, "Node disabled"

        return True, node

