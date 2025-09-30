# gui/client_gui.py
import tkinter as tk
from tkinter import ttk, messagebox
from transport.connection import Connection
import socket
import asyncio
import threading

THEMES = {
    "Light": {"bg": "white", "fg": "black", "input_bg": "white", "msg_bg": "#f0f0f0"},
    "Dark": {"bg": "#2b2b2b", "fg": "white", "input_bg": "#3b3b3b", "msg_bg": "#1e1e1e"},
    "Catogle": {"bg": "#fce8d8", "fg": "#4c3dc6", "input_bg": "#fff5e6", "msg_bg": "#f7d9b6"}
}

HOST_COLORS = ["yellow", "cyan", "magenta"]
CLIENT_COLORS = ["red", "blue", "green"]

class ChatGUI:
    def __init__(self, theme="Light"):
        self.theme = THEMES[theme]
        self.root = tk.Tk()
        self.root.title("CSCI4406 Chat - Connect")
        self.loop = asyncio.get_event_loop()
        self.conn = None
        self.username = ""
        self.user_type = "client"
        self.current_room = None
        self.create_connect_screen()
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def create_connect_screen(self):
        self.connect_frame = tk.Frame(self.root, bg=self.theme["bg"])
        self.connect_frame.pack(padx=10, pady=10)
        tk.Label(self.connect_frame, text="Server IP:", bg=self.theme["bg"], fg=self.theme["fg"]).grid(row=0, column=0)
        self.server_ip = tk.Entry(self.connect_frame)
        self.server_ip.insert(0, "127.0.0.1")
        self.server_ip.grid(row=0, column=1)
        tk.Label(self.connect_frame, text="Port:", bg=self.theme["bg"], fg=self.theme["fg"]).grid(row=1, column=0)
        self.server_port = tk.Entry(self.connect_frame)
        self.server_port.insert(0, "9000")
        self.server_port.grid(row=1, column=1)
        tk.Label(self.connect_frame, text="Username:", bg=self.theme["bg"], fg=self.theme["fg"]).grid(row=2, column=0)
        self.username_entry = tk.Entry(self.connect_frame)
        self.username_entry.grid(row=2, column=1)
        tk.Button(self.connect_frame, text="Connect", command=self.try_connect).grid(row=3, column=0, columnspan=2, pady=5)

    def try_connect(self):
        ip = self.server_ip.get()
        port = int(self.server_port.get())
        self.username = self.username_entry.get().strip()
        if not self.username:
            messagebox.showerror("Error", "Please enter a username")
            return
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setblocking(False)
        self.conn = Connection(self.loop, sock, (ip, port))
        self.conn.on_message(self.on_message)
        self.conn.send_msg(f"[CONNECT]{self.username}".encode())
        self.user_type = "host" if self.username.lower().startswith("host") else "client"
        self.on_connection_success()
        threading.Thread(target=self.start_loop, daemon=True).start()

    def start_loop(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_until_complete(self.conn.handle_receive())

    def on_connection_success(self):
        self.connect_frame.destroy()
        self.create_chat_screen()
        self.display_message(f"[SYSTEM] Connected as {self.username}", system=True)

    def create_chat_screen(self):
        self.chat_frame = tk.Frame(self.root, bg=self.theme["bg"])
        self.chat_frame.pack(expand=True, fill='both')

        # Chat box
        self.chat_box = tk.Text(self.chat_frame, state='disabled', bg=self.theme["msg_bg"], fg=self.theme["fg"])
        self.chat_box.pack(expand=True, fill='both')

        # Entry and send
        self.entry = tk.Entry(self.chat_frame, bg=self.theme["input_bg"], fg=self.theme["fg"])
        self.entry.pack(fill='x')
        self.entry.bind("<Return>", lambda e: self.send_message())

        # Room commands
        room_frame = tk.Frame(self.chat_frame, bg=self.theme["bg"])
        room_frame.pack(fill='x')
        tk.Button(room_frame, text="JOIN", command=self.join_room).pack(side='left')
        tk.Button(room_frame, text="LEAVE", command=self.leave_room).pack(side='left')
        tk.Button(room_frame, text="DM", command=self.send_dm_prompt).pack(side='left')

    def display_message(self, msg, system=False, username_type=None, username_color=None):
        self.chat_box.config(state='normal')
        if system:
            self.chat_box.insert('end', msg + "\n")
        else:
            if username_type and username_color:
                self.chat_box.insert('end', f"[{username_type.upper()}] ", ('username',))
                self.chat_box.tag_config('username', foreground=username_color)
            self.chat_box.insert('end', msg + "\n")
        self.chat_box.see('end')
        self.chat_box.config(state='disabled')

    def send_message(self):
        msg = self.entry.get().strip()
        if not msg:
            return
        if self.current_room:
            full_msg = f"[MSG]{self.current_room}:{self.username}:{msg}"
            self.conn.send_msg(full_msg.encode())
            self.display_message(f"{self.username}: {msg}", username_type=self.user_type,
                                 username_color=HOST_COLORS[0] if self.user_type=="host" else CLIENT_COLORS[0])
        else:
            messagebox.showwarning("No Room", "You must join a room first")
        self.entry.delete(0, 'end')

    def join_room(self):
        room = self.entry.get().strip()
        if not room:
            messagebox.showerror("Error", "Enter room name to join")
            return
        self.current_room = room
        self.conn.send_msg(f"[JOIN]{room}:{self.username}".encode())
        self.display_message(f"[SYSTEM] Joined room {room}", system=True)
        self.entry.delete(0, 'end')

    def leave_room(self):
        if not self.current_room:
            return
        self.conn.send_msg(f"[LEAVE]{self.current_room}:{self.username}".encode())
        self.display_message(f"[SYSTEM] Left room {self.current_room}", system=True)
        self.current_room = None

    def send_dm_prompt(self):
        to_user = self.entry.get().strip()
        if not to_user:
            messagebox.showerror("Error", "Enter username to DM")
            return
        dm_text = simpledialog.askstring("DM", f"Message to {to_user}:")
        if dm_text:
            self.conn.send_msg(f"[DM]{to_user}:{self.username}:{dm_text}".encode())
            self.display_message(f"[DM to {to_user}] {dm_text}", username_type=self.user_type,
                                 username_color=HOST_COLORS[0] if self.user_type=="host" else CLIENT_COLORS[0])
        self.entry.delete(0, 'end')

    def on_message(self, msg_bytes):
        msg = msg_bytes.decode()
        # Priority: presence updates
        if msg.startswith("[PRESENCE]"):
            self.display_message(msg, system=True)
        elif msg.startswith("[DM]"):
            self.display_message(msg)
        elif msg.startswith("[MSG]"):
            try:
                _, room_user, user_msg = msg.split(":", 2)
                username = room_user.split(",")[0]
                utype = room_user.split(",")[1] if "," in room_user else "client"
                color = HOST_COLORS[0] if utype=="host" else CLIENT_COLORS[0]
                self.display_message(f"{username}: {user_msg}", username_type=utype, username_color=color)
            except:
                self.display_message(msg)
        else:
            self.display_message(msg)

    def on_close(self):
        if self.conn:
            self.conn.send_msg(f"[DISCONNECT]{self.username}".encode())
            self.conn.close()
        self.root.destroy()


if __name__ == "__main__":
    gui = ChatGUI(theme="Catogle")
    gui.root.mainloop()
