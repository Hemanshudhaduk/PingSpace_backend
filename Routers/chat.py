# Routers/main.py
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    WebSocket,
    WebSocketDisconnect,
    Query,
    status,
    UploadFile,
    File,
    Form,
)
from jose.exceptions import JWTError
from sqlalchemy.orm import Session
from database import get_db
from jose import jwt
# from datetime import timezone

from models.user import User
from models.room import Room
from models.message import Message
from models.server import Server
from models.serveruser import ServerUser

from schemas.user_schema import UserOut, UserUpdate
from schemas.room_schema import RoomCreate, RoomResponse, RoomUpdate
from schemas.server_schema import ServerCreate, ServerResponse, ServerUpdate, UsersList
from schemas.message_schema import MessageResponse, MessageCreate, AttachmentResponse
from schemas.server_user_schema import ServerUserCreate, ServerUserResponse
from Routers.auth import hash_password

from ws.connection_manager import ConnectionManager
from Routers.auth import get_current_user, SECRET_KEY, ALGORITHM
from datetime import datetime, timedelta ,timezone
from collections import defaultdict


# upload a documet apis..
from models.attachment import Attachment
from services.cloudinary_service import (
    upload_to_cloudinary,
    get_message_type,
    MAX_IMAGE_SIZE,
    MAX_FILE_SIZE,
    MAX_VOICE_SIZE,
    ALLOWED_IMAGE_TYPES,
    ALLOWED_FILE_TYPES,
    ALLOWED_AUDIO_TYPES,
    ALLOWED_VIDEO_TYPES,
    ALL_ALLOWED_TYPES,
)


router = APIRouter()
manager = ConnectionManager()


# ------------------------
# USERS - Full CRUD
# ------------------------
@router.get("/users", response_model=list[UserOut], tags=["user"])
def get_all_users(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    return db.query(User).all()


@router.get("/users/{user_id}", response_model=UserOut, tags=["user"])
def get_user(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(404, "User not found")
    return user


@router.put("/users/{user_id}", response_model=UserOut, tags=["user"])
def update_user(
    user_id: str,
    payload: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(404, "User not found")
    if payload.username:
        user.username = payload.username

    if payload.password:
        user.password = hash_password(payload.password)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.delete("/users/{user_id}", tags=["user"])
def delete_user(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(404, "User not found")
    if current_user.id == user_id:
        db.delete(user)
        db.commit()
        return {"detail": "User deleted successfully"}
    raise HTTPException(status.HTTP_401_UNAUTHORIZED)


# ------------------------
# SERVERS - Full CRUD
# ------------------------
@router.post("/servers", response_model=ServerResponse, tags=["server"])
def create_server(
    data: ServerCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    print(data.name)
    if not data.name or data.name.strip() == "":
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, detail="Please enter the server name"
        )
    new_server = Server(name=data.name, admin_id=current_user.id)
    db.add(new_server)
    db.commit()
    db.refresh(new_server)
    # add admin as server user
    admin_link = ServerUser(
        user_id=current_user.id, server_id=new_server.id, role="admin"
    )
    db.add(admin_link)
    db.commit()
    return new_server


@router.get("/servers", response_model=list[ServerResponse], tags=["server"])
def get_servers(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    return (
        db.query(Server)
        .join(ServerUser, ServerUser.server_id == Server.id)
        .filter(ServerUser.user_id == current_user.id)
        .all()
    )


@router.get("/servers/{server_id}", response_model=ServerResponse, tags=["server"])
def get_server(
    server_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    server = db.query(Server).filter(Server.id == server_id).first()
    if not server:
        raise HTTPException(404, "Server not found")
    # check membership
    if (
        not db.query(ServerUser)
        .filter(
            ServerUser.server_id == server_id, ServerUser.user_id == current_user.id
        )
        .first()
    ):
        raise HTTPException(status_code=403, detail="Not a member of this server")
    return server


@router.put("/servers/{server_id}", response_model=ServerResponse, tags=["server"])
def update_server(
    server_id: str,
    payload: ServerUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    server = db.query(Server).filter(Server.id == server_id).first()

    if not server:
        raise HTTPException(404, "Server not found")
    if server.admin_id != current_user.id:
        raise HTTPException(403, "Only admin can update server")
    if not payload.name or payload.name.strip() == "":
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, detail="Please enter the server name"
        )
    if payload.name:
        server.name = payload.name
    db.add(server)
    db.commit()
    db.refresh(server)
    return server


@router.delete("/servers/{server_id}", tags=["server"])
def delete_server(
    server_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    server = db.query(Server).filter(Server.id == server_id).first()
    if not server:
        raise HTTPException(404, "Server not found")
    if server.admin_id != current_user.id:
        raise HTTPException(403, "Only the server admin can delete the server")
    # delete server users and rooms/messages cascade manually (simple approach)
    db.query(ServerUser).filter(ServerUser.server_id == server_id).delete(
        synchronize_session=False
    )

    room_ids = [
        r[0] for r in db.query(Room.id).filter(Room.server_id == server_id).all()
    ]
    if room_ids:
        db.query(Message).filter(Message.room_id.in_(room_ids)).delete(
            synchronize_session=False
        )

    db.query(Room).filter(Room.server_id == server_id).delete(synchronize_session=False)
    db.delete(server)
    db.commit()
    return {"detail": "Server deleted successfully"}


# ------------------------
# ROOMS - Full CRUD
# ------------------------
@router.post("/rooms", response_model=RoomResponse, tags=["room"])
def create_room(
    data: RoomCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    server = db.query(Server.admin_id).filter(Server.id == data.server_id).first()
    admin_check = (
        db.query(ServerUser)
        .filter(
            ServerUser.server_id == data.server_id,
            ServerUser.user_id == current_user.id,
            ServerUser.role == "admin",
        )
        .first()
    )
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")
    # only members can create rooms

    if not admin_check:
        raise HTTPException(status_code=403, detail="only admin can make the room")
    if (
        db.query(Room)
        .filter(Room.server_id == data.server_id, Room.name == data.name)
        .first()
    ):
        raise HTTPException(status_code=400, detail="Room already exists")
    new_room = Room(
        name=data.name, description=data.description or "", server_id=data.server_id
    )
    db.add(new_room)
    db.commit()
    db.refresh(new_room)
    return new_room


@router.get("/rooms/{server_id}", response_model=list[RoomResponse], tags=["room"])
def get_rooms_by_server(
    server_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if (
        not db.query(ServerUser)
        .filter(
            ServerUser.server_id == server_id, ServerUser.user_id == current_user.id
        )
        .first()
    ):
        raise HTTPException(status_code=403, detail="Not a member of server")
    return db.query(Room).filter(Room.server_id == server_id).all()


@router.get("/room/{room_id}", response_model=RoomResponse, tags=["room"])
def get_room(
    room_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        raise HTTPException(404, "Room not found")
    if (
        not db.query(ServerUser)
        .filter(
            ServerUser.server_id == room.server_id,
            ServerUser.user_id == current_user.id,
        )
        .first()
    ):
        raise HTTPException(status_code=403, detail="Not a member of server")
    return room


@router.put("/rooms/{room_id}", response_model=RoomResponse, tags=["room"])
def update_room(
    room_id: str,
    payload: RoomUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        raise HTTPException(404, "Room not found")
    server = db.query(Server).filter(Server.id == room.server_id).first()
    if server.admin_id != current_user.id:
        raise HTTPException(403, "Only server admin can update rooms")
    if payload.name:
        room.name = payload.name
    if payload.description is not None:
        room.description = payload.description
    db.add(room)
    db.commit()
    db.refresh(room)
    return room


@router.delete("/rooms/{room_id}", tags=["room"])
def delete_room(
    room_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        raise HTTPException(404, "Room not found")
    server = db.query(Server).filter(Server.id == room.server_id).first()
    if server.admin_id != current_user.id:
        raise HTTPException(403, "Only server admin can delete rooms")
    db.query(Message).filter(Message.room_id == room.id).delete()
    db.delete(room)
    db.commit()
    return {"detail": "Room deleted successfully"}


# ------------------------
# MESSAGES - CRUD
# ------------------------
@router.post("/messages", response_model=MessageResponse, tags=["message"])
def post_message(
    payload: MessageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    room = db.query(Room).filter(Room.id == payload.room_id).first()
    if not room:
        raise HTTPException(404, "Room not found")
    membership = (
        db.query(ServerUser)
        .filter(
            ServerUser.user_id == current_user.id,
            ServerUser.server_id == room.server_id,
        )
        .first()
    )
    if not membership:
        raise HTTPException(status_code=401, detail="not member of a server")

    if not payload.content or len(payload.content) > 0:
        raise HTTPException(400, "Message content invalid")
    print("This is the payload : ", payload)
    new_msg = Message(
        room_id=payload.room_id, sender=current_user.username, content=payload.content
    )

    db.add(new_msg)
    db.commit()
    db.refresh(new_msg)
    return new_msg


@router.get(
    "/messages/{room_id}", response_model=list[MessageResponse], tags=["message"]
)
def get_history(
    room_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    before: str = Query(None),  # cursor for pagination
    limit: int = Query(50, le=100),
):
    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        raise HTTPException(404, "Room not found")

    if (
        not db.query(ServerUser)
        .filter(
            ServerUser.user_id == current_user.id,
            ServerUser.server_id == room.server_id,
        )
        .first()
    ):
        raise HTTPException(403, "Not a member of this server")
    query = db.query(Message).filter(Message.room_id == room_id)
    if before:
        query = query.filter(Message.timestamp < before)

    messages = query.order_by(Message.timestamp.desc()).limit(limit).all()

    result = []

    for msg in messages:
        att = None
        if msg.type != "text":
            att_row = (
                db.query(Attachment).filter(Attachment.message_id == msg.id).first()
            )
            if att_row:
                att = AttachmentResponse.model_validate(att_row)
        result.append(
            MessageResponse(
                id=msg.id,
                room_id=msg.room_id,
                sender=msg.sender,
                content=msg.content,
                type=msg.type,
                timestamp=msg.timestamp,
                attachment=att,
            )
        )
    return result


@router.delete("/messages/{message_id}", tags=["message"])
def delete_message(
    message_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    msg = db.query(Message).filter(Message.id == message_id).first()
    if not msg:
        raise HTTPException(404, "Message not found")

    room = db.query(Room).filter(Room.id == msg.room_id).first()
    if not room:
        raise HTTPException(404, "Room not found")

    is_sender = msg.sender == current_user.username
    is_admin = (
        db.query(ServerUser)
        .filter(
            ServerUser.user_id == current_user.id,
            ServerUser.server_id == room.server_id,
            ServerUser.role == "admin",
        )
        .first()
    )

    if not (is_sender or is_admin):
        raise HTTPException(403, "Not authorized to delete message")

    db.delete(msg)
    db.commit()

    return {
        "detail": "Message deleted by admin"
        if is_admin and not is_sender
        else "Message deleted"
    }


# ------------------------
# SERVER USERS
# ------------------------
@router.post("/server_users", response_model=ServerUserResponse, tags=["server user"])
def create_server_user(
    payload: ServerUserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # only server admin or admin can add
    server = db.query(Server).filter(Server.id == payload.server_id).first()
    if not server:
        raise HTTPException(404, "Server not found")
    # Allow if the user is adding themselves as a "member" using an invite link
    is_self_join = payload.user_id == current_user.id and payload.role == "member"

    # Or allow if the current user is an admin adding someone else
    admin_check = (
        db.query(ServerUser)
        .filter(
            ServerUser.server_id == payload.server_id,
            ServerUser.user_id == current_user.id,
        )
        .first()
    )
    is_admin = admin_check and (
        server.admin_id == current_user.id or admin_check.role == "admin"
    )

    if not (is_self_join or is_admin):
        raise HTTPException(
            403,
            "Not allowed: Only an admin can add other users, or you can join as a member yourself",
        )

    if (
        db.query(ServerUser)
        .filter(
            ServerUser.user_id == payload.user_id,
            ServerUser.server_id == payload.server_id,
        )
        .first()
    ):
        raise HTTPException(409, "User already in server")
    su = ServerUser(
        user_id=payload.user_id, server_id=payload.server_id, role=payload.role
    )
    db.add(su)
    db.commit()
    db.refresh(su)
    return su


@router.get(
    "/server_users/{user_id}",
    response_model=list[ServerUserResponse],
    tags=["server user"],
)
def get_servers_for_user(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    if user_id != current_user.id:
        ok = (
            db.query(ServerUser)
            .filter(ServerUser.user_id == current_user.id, ServerUser.role == "admin")
            .first()
        )
        if not ok:
            raise HTTPException(403, "Not authorized")

    return db.query(ServerUser).filter(ServerUser.user_id == user_id).all()


@router.get(
    "/server_user/{server_id}", response_model=list[UsersList], tags=["server user"]
)
def get_users_list(
    server_id,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    results = (
        db.query(User.id, User.username, ServerUser.role)
        .join(ServerUser, ServerUser.user_id == User.id)
        .filter(ServerUser.server_id == server_id)
        .all()
    )
    return [UsersList(id=r[0], username=r[1], role=r[2]) for r in results]


@router.delete("/server_users/{su_id}", tags=["server user"])
def delete_server_user(
    su_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    su = db.query(ServerUser).filter(ServerUser.id == su_id).first()
    if not su:
        raise HTTPException(404, "ServerUser not found")
    server = db.query(Server).filter(Server.id == su.server_id).first()
    if server.admin_id != current_user.id and current_user.id != su.user_id:
        raise HTTPException(
            403, "Only admin or the user themselves can remove membership"
        )
    db.delete(su)
    db.commit()
    return {"detail": "Server user removed"}


@router.post("/upload", tags=["upload"])
async def upload_file(
    file: UploadFile = File(...),
    room_id: str = Form(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # 1. Validate mime type
    mime_type = file.content_type or ""
    if mime_type not in ALL_ALLOWED_TYPES:
        raise HTTPException(400, f"File type not allowed: {mime_type}")

    # 2. Read file and check size
    file_bytes = await file.read()
    file_size = len(file_bytes)

    if mime_type in ALLOWED_IMAGE_TYPES and file_size > MAX_IMAGE_SIZE:
        raise HTTPException(400, "Image too large. Max 10MB")
    if mime_type in ALLOWED_AUDIO_TYPES and file_size > MAX_VOICE_SIZE:
        raise HTTPException(400, "Voice too large. Max 10MB")
    if file_size > MAX_FILE_SIZE:
        raise HTTPException(400, "File too large. Max 50MB")

    # 3. Check membership
    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        raise HTTPException(404, "Room not found")
    if (
        not db.query(ServerUser)
        .filter(
            ServerUser.user_id == current_user.id,
            ServerUser.server_id == room.server_id,
        )
        .first()
    ):
        raise HTTPException(403, "Not a member of this server")

    # 4. Upload to Cloudinary
    try:
        upload_result = upload_to_cloudinary(
            file_bytes, mime_type, file.filename or "file"
        )
    except Exception as e:
        raise HTTPException(500, f"Upload failed: {str(e)}")

    msg_type = get_message_type(mime_type)

    # 5. Save message row
    new_msg = Message(
        room_id=room_id,
        sender=current_user.username,
        content=None,
        type=msg_type,
    )
    db.add(new_msg)
    db.commit()
    db.refresh(new_msg)

    # 6. Save attachment row
    attachment = Attachment(
        message_id=new_msg.id,
        file_url=upload_result["file_url"],
        file_name=file.filename or "file",
        file_size=file_size,
        mime_type=mime_type,
        width=upload_result.get("width"),
        height=upload_result.get("height"),
        duration=upload_result.get("duration"),
    )
    db.add(attachment)
    db.commit()
    db.refresh(attachment)

    broadcast = {
        "id": new_msg.id,
        "sender": current_user.username,
        "content": None,
        "type": msg_type,
        "created_at": new_msg.timestamp.replace(tzinfo=timezone.utc).isoformat(),
        "attachment": {
            "file_url": attachment.file_url,
            "file_name": attachment.file_name,
            "file_size": attachment.file_size,
            "mime_type": attachment.mime_type,
            "width": attachment.width,
            "height": attachment.height,
            "duration": attachment.duration,
        },
    }
    await manager.broadcast(room_id, broadcast)
    return broadcast


# ------------------------
# WEBSOCKET CHAT
# ------------------------


class RateLimiter:
    def __init__(self):
        self.user_messages = defaultdict(list)

    def can_send_message(
        self, username: str, max_messages: int = 1000, seconds: int = 10
    ) -> bool:

        now = datetime.now()
        cutoff_time = now - timedelta(seconds=seconds)

        # Remove old messages outside the time window
        self.user_messages[username] = [
            msg_time
            for msg_time in self.user_messages[username]
            if msg_time > cutoff_time
        ]

        if len(self.user_messages[username]) >= max_messages:
            return False

        self.user_messages[username].append(now)
        return True


rate_limiter = RateLimiter()


@router.websocket("/ws/{room_id}")
async def chat_socket(
    websocket: WebSocket,
    room_id: str,
    token: str = Query(...),
    db: Session = Depends(get_db),
):

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("username")
        print("Decoded username:", username)
        if username is None:
            await websocket.close(
                code=status.WS_1008_POLICY_VIOLATION,
                reason="Invalid token: username not found",
            )
            return
    except (JWTError, jwt.InvalidTokenError) as e:
        await websocket.close(
            code=status.WS_1008_POLICY_VIOLATION, reason=f"Invalid token: {str(e)}"
        )
        return

    user = db.query(User).filter(User.username == username).first()
    if not user:
        await websocket.close(
            code=status.WS_1008_POLICY_VIOLATION, reason="User not found"
        )
        return

    room_obj = db.query(Room).filter(Room.id == room_id).first()
    if not room_obj:
        await websocket.close(
            code=status.WS_1008_POLICY_VIOLATION, reason="Room not found"
        )
        return

    membership = (
        db.query(ServerUser)
        .filter(
            ServerUser.user_id == user.id, ServerUser.server_id == room_obj.server_id
        )
        .first()
    )

    if not membership:
        await websocket.close(
            code=status.WS_1008_POLICY_VIOLATION, reason="Not a member of this server"
        )
        return

    await websocket.accept()

    await manager.connect(websocket, room_id, username)
    try:
        while True:
            msg_text = await websocket.receive_text()

            if not rate_limiter.can_send_message(username):
                await websocket.send_json(
                    {
                        "error": "You're sending messages too fast. Please slow down.",
                        "type": "rate_limit",
                    }
                )
                continue

            new_msg = Message(room_id=room_obj.id, sender=username, content=msg_text)
            db.add(new_msg)
            db.commit()
            db.refresh(new_msg)
            broadcast = {
                "id": new_msg.id,
                "sender": username,
                "content": msg_text,
                "created_at": new_msg.timestamp.replace(
                    tzinfo=timezone.utc
                ).isoformat(),
            }
            await manager.broadcast(room_id, broadcast)

    except WebSocketDisconnect:
        manager.disconnect(websocket, room_id)
    except Exception as e:
        print(f"Error in chat_socket: {e}")
        manager.disconnect(websocket, room_id)
