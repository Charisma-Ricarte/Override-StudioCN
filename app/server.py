# app/server.py (update)
ROOM_HISTORY_SIZE = 20

class ServerLogic:
    def __init__(self):
        self.rooms = {}  # room_name -> Room
        self.users = {}  # username -> User

    def join_room(self, username, room_name):
        user = self.users[username]
        room = self.rooms[room_name]
        if username not in room.members:
            room.members.append(username)
            # Send last N messages
            for msg in room.history[-ROOM_HISTORY_SIZE:]:
                user.conn.send_msg(msg.encode())
            # Presence notification
            self.broadcast(room_name, f"[PRESENCE] {username} joined")

    def leave_room(self, username, room_name):
        user = self.users[username]
        room = self.rooms[room_name]
        if username in room.members:
            room.members.remove(username)
            self.broadcast(room_name, f"[PRESENCE] {username} left")

    def broadcast(self, room_name, msg):
        room = self.rooms[room_name]
        room.history.append(msg)
        for uname in room.members:
            user = self.users[uname]
            if user.conn:
                user.conn.send_msg(msg.encode())

    def send_dm(self, from_user, to_user, msg):
        if to_user in self.users:
            self.users[to_user].conn.send_msg(f"[DM from {from_user}] {msg}".encode())
