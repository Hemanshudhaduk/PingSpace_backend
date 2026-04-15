from fastapi import WebSocket
from datetime import datetime

class ConnectionManager:
    def __init__(self):
        self.rooms = {} #{(room_id) : [sockets]}
        self.socket_to_username = {} #{socket: username}
        self.typing_users = {}  # {room_id: {username: timestamp}}

    async def connect(self, websocket: WebSocket, room_id :str , username:str):
        # Note: websocket.accept() should be called in the endpoint before calling this method

        # key = (server_id, room)

        if room_id not in self.rooms:
            self.rooms[room_id] = []
            self.typing_users[room_id] = {}

        self.rooms[room_id].append(websocket)
        print("This are self.rooms" , self.rooms)
    

        self.socket_to_username[websocket] = username


    def disconnect(self, websocket: WebSocket, room_id: str):
        username = self.socket_to_username.get(websocket)

        if room_id in self.rooms and websocket in self.rooms[room_id]:
            self.rooms[room_id].remove(websocket)
        
        # Clear typing status when user disconnects
        if username and room_id in self.typing_users:
            self.typing_users[room_id].pop(username, None)

    # Track when user starts typing
    def set_typing(self, room_id: str, username: str):
        if room_id not in self.typing_users:
            self.typing_users[room_id] = {}
        self.typing_users[room_id][username] = datetime.utcnow()

    # Clear typing status
    def clear_typing(self, room_id: str, username: str):
        if room_id in self.typing_users:
            self.typing_users[room_id].pop(username, None)

    # Get currently typing users (ignoring timed-out entries)
    def get_typing_users(self, room_id: str, timeout_seconds: int = 5) -> list:
        if room_id not in self.typing_users:
            return []
        
        now = datetime.utcnow()
        active_typists = []
        stale = []
        
        for username, timestamp in self.typing_users[room_id].items():
            if (now - timestamp).total_seconds() < timeout_seconds:
                active_typists.append(username)
            else:
                stale.append(username)
        
        # Clean up stale entries
        for username in stale:
            self.typing_users[room_id].pop(username, None)
        
        return active_typists

    async def broadcast(self, room_id: str, message):
        # key = (server_id, room)

        if room_id not in self.rooms:
            return

        stale = []

        for connection in list(self.rooms[room_id]):
            try:
                await connection.send_json(message)
            except Exception:
                stale.append(connection)

        for connection in stale:
            try:
                await connection.close()
            except:
                pass
            self.disconnect(connection, room_id)

    def get_all_the_rooms(self):
        return self.rooms

    def check_new(self, server_id: str, room: str, username: str):
        key = (server_id, room)
        return key not in self.online or username not in self.online[key]


manager = ConnectionManager()
