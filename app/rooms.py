# app/rooms.py
class Room:
    def __init__(self, name, host):
        self.name = name
        self.host = host
        self.members = []      # usernames
        self.history = []      # last N messages

class User:
    def __init__(self, username, utype, color, conn=None):
        self.username = username
        self.type = utype      # 'host' or 'client'
        self.color = color
        self.conn = conn
