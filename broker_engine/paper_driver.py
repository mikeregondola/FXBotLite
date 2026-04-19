import requests


class TelegramBot:

    def __init__(self, chat_id, bot_token):
        self.chat_id = chat_id
        self.bot_token = bot_token
        self.base_url = f"https://api.telegram.org/bot{bot_token}"
        self.last_update_id = None

    # --------------------------------------------------
    # SEND MESSAGE
    # --------------------------------------------------
    def send_message(self, text, chat_id=None):

        if chat_id is None:
            chat_id = self.chat_id

        try:
            url = f"{self.base_url}/sendMessage"

            payload = {
                "chat_id": chat_id,
                "text": text
            }

            response = requests.post(url, json=payload)

            print("[TG SEND STATUS]", response.status_code)
            print("[TG SEND RESPONSE]", response.text)

        except Exception as e:
            print(f"[TG ERROR] {e}")

    # --------------------------------------------------
    # HANDLE COMMANDS
    # --------------------------------------------------
    def handle_commands(self, node_manager):

        try:
            url = f"{self.base_url}/getUpdates"

            params = {}
            if self.last_update_id is not None:
                params["offset"] = self.last_update_id + 1

            response = requests.get(url, params=params).json()

            print("[TG RAW]", response)

            if not response.get("ok"):
                return

            results = response.get("result", [])

            # ---------------- FIRST RUN ----------------
            if self.last_update_id is None and results:

                print("[TG] First run → processing latest message only")

                item = results[-1]
                self.last_update_id = item["update_id"]

                message = item.get("message")
                if not message:
                    return

                chat_id = message["chat"]["id"]
                text = message.get("text", "")

                self.chat_id = chat_id

                print(f"[TG] Active chat_id set to: {chat_id}")
                print(f"[TG] Received: {text}")

                self._handle_user(text, chat_id, node_manager)
                return

            # ---------------- NORMAL LOOP ----------------
            for item in results:

                update_id = item["update_id"]

                if self.last_update_id is not None and update_id <= self.last_update_id:
                    continue

                self.last_update_id = update_id

                message = item.get("message")
                if not message:
                    continue

                chat_id = message["chat"]["id"]
                text = message.get("text", "")

                self.chat_id = chat_id

                print(f"[TG] Active chat_id set to: {chat_id}")
                print(f"[TG] Received: {text}")

                self._handle_user(text, chat_id, node_manager)

        except Exception as e:
            print("[TG ERROR]", e)

    # --------------------------------------------------
    # USER COMMAND HANDLER
    # --------------------------------------------------
    def _handle_user(self, text, chat_id, node_manager):

        # ---------- START ----------
        if text == "/start":

            if node_manager.is_registered(chat_id):

                self.send_message(
                    "🤖 Welcome back to StructuraFX\n\n"
                    "📊 You will receive delayed trade signals.\n\n"
                    "🚀 Upgrade to PRO for auto trading:\n"
                    "/upgrade",
                    chat_id=chat_id
                )

            else:

                self.send_message(
                    "🤖 Welcome to StructuraFX\n\n"
                    "👉 /register — Create your node",
                    chat_id=chat_id
                )

        # ---------- REGISTER ----------
        elif text == "/register":

            if node_manager.is_registered(chat_id):
                self.send_message(
                    "⚠️ You are already registered.\n\n"
                    "Use /upgrade to unlock PRO features.",
                    chat_id=chat_id
                )
                return

            node_id, api_key = node_manager.register_node(chat_id)

            self.send_message(
                f"✅ Registered!\n\n"
                f"Node ID: {node_id}\n"
                f"API Key: {api_key}\n\n"
                f"📊 You will now receive delayed signals.\n"
                f"🚀 Upgrade to PRO for auto trading.",
                chat_id=chat_id
            )

        # ---------- UPGRADE ----------
        elif text == "/upgrade":

            self.send_message(
                "🚀 PRO Upgrade\n\n"
                "Unlock:\n"
                "✔ Auto trade execution\n"
                "✔ Break-even automation\n"
                "✔ Trailing stop\n\n"
                "Contact admin to activate PRO.",
                chat_id=chat_id
            )

# Telegram_bot.py
