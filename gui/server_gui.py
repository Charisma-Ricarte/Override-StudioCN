# gui/server_gui.py
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from transport.connection import Connection
import socket
import asyncio
import threading

HOST_COLORS = ["yellow", "cyan", "magenta"]
CLIENT_COLORS = ["red", "blue", "green"]

class User:
    def __init__(self, username, conn, user_type="client"):
        self.username = username
        self.conn = conn
        self.user_type = user_type
        self.rooms = set()

class Room:
    def __init__(self, name):
        self.name = name
        self.members = set()  # usernames
        self.history = []

class ServerGUI:
    def __init__(self, port=9000):
        self.loop = asyncio.get_event_loop()
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(("0.0.0.0", port))
        self.sock.setblocking(False)

        self.users = {}  # username -> User
        self.rooms = {}  # room_name -> Room

        self.root = tk.Tk()
        self.root.title("CSCI4406 Chat Server")
        self.create_gui()
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        threading.Thread(target=self.start_loop, daemon=True).start()

    def create_gui(self):
        self.chat_box = tk.Text(self.root, state='disabled', height=20)
        self.chat_box.pack(expand=True, fill='both')

        control_frame = tk.Frame(self.root)
        control_frame.pack(fill='x')
        tk.Button(control_frame, text="Create Room", command=self.create_room_prompt).pack(side='left')
        tk.Button(control_frame, text="Send Message", command=self.send_message_prompt).pack(side='left')

    def display_message(self, msg, username_type=None, username_color=None):
        self.chat_box.config(state='normal')
        if username_type and username_color:
            self.chat_box.insert('end', f"[{username_type.upper()}] ", ('username',))
            self.chat_box.tag_config('username', foreground=username_color)
        self.chat_box.insert('end', msg + "\n")
        self.chat_box.see('end')
        self.chat_box.config(state='disabled')

    def start_loop(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_until_complete(self.handle_receive())

    async def handle_receive(self):
        while True:
            try:
                data, addr = await self.loop.sock_recvfrom(self.sock, 4096)
                self.process_message(data.decode(), addr)
            except Exception as e:
                print("Receive error:", e)

    def process_message(self, msg, addr):
        if msg.startswith("[CONNECT]"):
            username = msg.replace("[CONNECT]", "")
            user_type = "host" if username.lower().startswith("host") else "client"
            conn = Connection(self.loop, self.sock, addr)
            user = User(username, conn, user_type)
            self.users[username] = user
            self.display_message(f"[SYSTEM] {username} connected", username_type=user_type,
                                 username_color=HOST_COLORS[0] if user_type=="host" else CLIENT_COLORS[0])
        elif msg.startswith("[JOIN]"):
            room_name, username = msg.replace("[JOIN]", "").split(":")
            if room_name not in self.rooms:
                self.rooms[room_name] = Room(room_name)
            room = self.rooms[room_name]
            user = self.users[username]
            room.members.add(username)
            user.rooms.add(room_name)
            # Send last N messages
            for history_msg in room.history[-20:]:
                user.conn.send_msg(history_msg.encode())
            # Notify presence
            self.broadcast(room_name, f"[PRESENCE] {username} joined")
        elif msg.startswith("[LEAVE]"):
            room_name, username = msg.replace("[LEAVE]", "").split(":")
            room = self.rooms.get(room_name)
            if room:
                room.members.discard(username)
                self.users[username].rooms.discard(room_name)
                self.broadcast(room_name, f"[PRESENCE] {username} left")
        elif msg.startswith("[MSG]"):
            try:
                room, username, text = msg.replace("[MSG]", "").split(":", 2)
                self.broadcast(room, f"{username}: {text}", sender=username)
            except:
                print("Malformed MSG:", msg)
        elif msg.startswith("[DM]"):
            try:
                to_user, from_user, text = msg.replace("[DM]", "").split(":", 2)
                if to_user in self.users:
                    self.users[to_user].conn.send_msg(f"[DM from {from_user}] {text}".encode())
            except:
                print("Malformed DM:", msg)
        elif msg.startswith("[DISCONNECT]"):
            username = msg.replace("[DISCONNECT]", "")
            user = self.users.pop(username, None)
            if user:
                for room_name in user.rooms:
                    self.rooms[room_name].members.discard(username)
                    self.broadcast(room_name, f"[PRESENCE] {username} disconnected")

    def broadcast(self, room_name, msg, sender=None):
        room = self.rooms.get(room_name)
        if not room:
            return
        room.history.append(msg)
        for uname in room.members:
            user = self.users.get(uname)
            if user and user.conn:
                user.conn.send_msg(msg.encode())
        self.display_message(msg, username_type="host" if sender and sender.lower().startswith("host") else "client",
                             username_color=HOST_COLORS[0] if sender and sender.lower().startswith("host") else CLIENT_COLORS[0])

    def create_room_prompt(self):
        room_name = simpledialog.askstring("Create Room", "Room name:")
        if room_name:
            if room_name in self.rooms:
                messagebox.showerror("Error", "Room already exists")
                return
            self.rooms[room_name] = Room(room_name)
            self.display_message(f"[SYSTEM] Room {room_name} created", system=True)

    def send_message_prompt(self):
        room_name = simpledialog.askstring("Send Message", "Room name:")
        text = simpledialog.askstring("Send Message", "Message:")
        if room_name and text:
            self.broadcast(room_name, f"[HOST] {text}", sender="host")

    def on_close(self):
        for user in self.users.values():
            if user.conn:
                user.conn.send_msg(f"[DISCONNECT]Server shutting down".encode())
                user.conn.close()
        self.sock.close()
        self.root.destroy()


if __name__ == "__main__":
    gui = ServerGUI(port=9000)
    gui.root.mainloop()
