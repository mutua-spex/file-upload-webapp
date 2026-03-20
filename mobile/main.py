import os
import re
import threading
import time
from functools import partial

import cache
import requests
from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.metrics import dp
from kivy.properties import StringProperty
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.image import AsyncImage
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import Screen, ScreenManager

from plyer import notification
from websocket import WebSocketApp

# Adjust this to match where your backend runs (localhost for dev)
BACKEND_URL = os.environ.get("CHAT_BACKEND_URL", "http://127.0.0.1:8000")

KV_FILE = os.path.join(os.path.dirname(__file__), "chat.kv")


class LoginScreen(Screen):
    def login(self, username: str, password: str) -> None:
        if not username or not password:
            self._show_error("Username and password are required")
            return

        resp = requests.post(
            f"{BACKEND_URL}/api/auth/token",
            json={"username": username, "password": password},
            timeout=10,
        )
        if resp.status_code != 200:
            self._show_error(resp.json().get("detail", "Login failed"))
            return

        data = resp.json()
        app = App.get_running_app()
        app.token = data["access_token"]
        app.username = username
        app.root.current = "rooms"
        app.root.get_screen("rooms").load_rooms()

    def register(self, username: str, password: str) -> None:
        if not username or not password:
            self._show_error("Username and password are required")
            return

        resp = requests.post(
            f"{BACKEND_URL}/api/auth/register",
            json={"username": username, "password": password},
            timeout=10,
        )
        if resp.status_code != 200:
            self._show_error(resp.json().get("detail", "Registration failed"))
            return

        self._show_info("Registration successful. You can now log in.")

    def _show_error(self, message: str) -> None:
        popup = Popup(title="Error", content=Label(text=message), size_hint=(0.8, 0.3))
        popup.open()

    def _show_info(self, message: str) -> None:
        popup = Popup(title="Info", content=Label(text=message), size_hint=(0.8, 0.3))
        popup.open()


class RoomsScreen(Screen):
    def load_rooms(self) -> None:
        app = App.get_running_app()
        headers = {"Authorization": f"Bearer {app.token}"}
        try:
            resp = requests.get(f"{BACKEND_URL}/api/rooms", headers=headers, timeout=10)
        except Exception as e:
            self._show_error(f"Unable to load rooms: {e}")
            return

        if resp.status_code != 200:
            self._show_error(resp.text)
            return

        rooms = resp.json()
        rooms_box = self.ids.rooms_box
        rooms_box.clear_widgets()
        for room in rooms:
            btn = LabelButton(text=room["name"], size_hint_y=None, height=dp(40))
            btn.bind(on_release=partial(self.open_room, room))
            rooms_box.add_widget(btn)

    def create_room(self, name: str) -> None:
        if not name:
            return
        app = App.get_running_app()
        headers = {"Authorization": f"Bearer {app.token}"}
        resp = requests.post(
            f"{BACKEND_URL}/api/rooms", json={"name": name}, headers=headers, timeout=10
        )
        if resp.status_code != 200:
            self._show_error(resp.text)
            return
        self.load_rooms()

    def open_room(self, room: dict, *_) -> None:
        app = App.get_running_app()
        chat_screen = app.root.get_screen("chat")
        chat_screen.room_id = room["id"]
        chat_screen.room_name = room["name"]
        app.root.current = "chat"
        chat_screen.connect_websocket()

    def _show_error(self, message: str) -> None:
        popup = Popup(title="Error", content=Label(text=message), size_hint=(0.8, 0.3))
        popup.open()


class ChatScreen(Screen):
    room_id: int = 0
    room_name = StringProperty("")
    presence: list[dict] = []
    _seen_message_ids: set[int] = set()

    def on_pre_enter(self) -> None:
        self.ids.messages_box.clear_widgets()
        self._seen_message_ids.clear()
        self.presence = []

    def connect_websocket(self) -> None:
        app = App.get_running_app()
        token = app.token
        if not token:
            return

        url = f"ws://{BACKEND_URL.split('://', 1)[1]}/ws/{self.room_id}?token={token}"

        def on_message(ws, message):
            Clock.schedule_once(lambda dt: self._handle_message(message), 0)

        def on_error(ws, error):
            Clock.schedule_once(lambda dt: self._show_popup("WebSocket error", str(error)), 0)

        def on_close(ws, close_status_code, close_msg):
            Clock.schedule_once(lambda dt: self._show_popup("Disconnected", "Connection closed"), 0)

        self.ws_app = WebSocketApp(
            url,
            on_message=on_message,
            on_error=on_error,
            on_close=on_close,
        )

        # Run websocket in a background thread.
        self.ws_thread = threading.Thread(target=self.ws_app.run_forever, daemon=True)
        self.ws_thread.start()

        # Load recent messages
        self.load_history()

    def load_history(self) -> None:
        # Load cached messages first for offline support.
        for msg in cache.get_messages(self.room_id):
            self._add_message(msg)

        app = App.get_running_app()
        headers = {"Authorization": f"Bearer {app.token}"}
        try:
            resp = requests.get(
                f"{BACKEND_URL}/api/rooms/{self.room_id}/messages", headers=headers, timeout=10
            )
            if resp.status_code == 200:
                for msg in resp.json():
                    self._add_message(msg)
        except Exception:
            # offline / server not reachable
            pass

    def send_message(self, text: str) -> None:
        if not text and not getattr(self, "attachment_url", None):
            return
        if not hasattr(self, "ws_app"):
            self._show_popup("Error", "Not connected to the room")
            return

        payload = {"content": text}
        if getattr(self, "attachment_url", None):
            payload["attachment_url"] = self.attachment_url
            self.attachment_url = None

        try:
            self.ws_app.send(str(payload).replace("'", '"'))
        except Exception as e:
            self._show_popup("Send failed", str(e))

    def _handle_message(self, message: str) -> None:
        try:
            import json

            obj = json.loads(message)
        except Exception:
            return

        msg_type = obj.get("type")
        if msg_type == "message":
            self._add_message(obj.get("message", {}))
            if self.manager.current != "chat":
                self._show_notification("New message", "You have a new message")
        elif msg_type in ("user_joined", "user_left"):
            self.presence = obj.get("presence", [])
        elif msg_type == "presence":
            self.presence = obj.get("presence", [])

    def _add_message(self, msg: dict) -> None:
        text = msg.get("content") or ""
        sender_id = msg.get("sender_id")
        attachment = msg.get("attachment_url")
        label_text = f"[{sender_id}] {text}"
        if attachment:
            label_text += f" \nAttachment: {BACKEND_URL}{attachment}"
        lbl = Label(text=label_text, size_hint_y=None, height=dp(60), text_size=(Window.width - dp(32), None))
        self.ids.messages_box.add_widget(lbl)
        Clock.schedule_once(lambda dt: self.ids.messages_box.parent.scroll_to(lbl), 0.1)

    def pick_file(self) -> None:
        from kivy.uix.boxlayout import BoxLayout
        from kivy.uix.button import Button
        from kivy.uix.filechooser import FileChooserListView

        content = BoxLayout(orientation="vertical")
        filechooser = FileChooserListView(path=os.path.expanduser("~"), filters=["*.*"])
        buttons = BoxLayout(size_hint_y=None, height=dp(40), spacing=8)
        btn_cancel = Button(text="Cancel")
        btn_upload = Button(text="Upload")
        buttons.add_widget(btn_cancel)
        buttons.add_widget(btn_upload)
        content.add_widget(filechooser)
        content.add_widget(buttons)

        popup = Popup(title="Select a file to upload", content=content, size_hint=(0.9, 0.9))

        def _do_upload(*_):
            selection = filechooser.selection
            if not selection:
                return
            popup.dismiss()
            self._upload_file(selection[0])

        btn_cancel.bind(on_release=lambda *_: popup.dismiss())
        btn_upload.bind(on_release=_do_upload)
        popup.open()

    def _upload_file(self, path: str) -> None:
        app = App.get_running_app()
        headers = {"Authorization": f"Bearer {app.token}"}
        try:
            with open(path, "rb") as f:
                files = {"file": (os.path.basename(path), f)}
                resp = requests.post(f"{BACKEND_URL}/api/upload", files=files, headers=headers, timeout=30)
            if resp.status_code == 200:
                self.attachment_url = resp.json().get("url")
                self._show_popup("Uploaded", "Attachment ready to send")
            else:
                self._show_popup("Upload failed", resp.text)
        except Exception as e:
            self._show_popup("Upload failed", str(e))

    def _show_popup(self, title: str, message: str) -> None:
        popup = Popup(title=title, content=Label(text=message), size_hint=(0.8, 0.3))
        popup.open()


class LabelButton(ButtonBehavior, Label):
    pass


class ChatApp(App):
    token: str = ""
    username: str = ""

    def build(self):
        cache.init_cache()
        Builder.load_file(KV_FILE)
        sm = ScreenManager()
        sm.add_widget(LoginScreen(name="login"))
        sm.add_widget(RoomsScreen(name="rooms"))
        sm.add_widget(ChatScreen(name="chat"))
        return sm


if __name__ == "__main__":
    ChatApp().run()
