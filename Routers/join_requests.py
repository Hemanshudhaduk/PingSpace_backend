from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models.join_request import JoinRequest
from models.server import Server
from models.serveruser import ServerUser
from models.user import User
from schemas.join_request_schema import JoinRequestCreate, JoinRequestOut, JoinRequestUpdate
from Routers.auth import get_current_user

router = APIRouter()

@router.post("/join_requests", response_model=JoinRequestOut)
def create_join_request(request: JoinRequestCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Check if user already in server
    existing = db.query(ServerUser).filter(ServerUser.server_id == request.server_id, ServerUser.user_id == current_user.id).first()
    if existing:
        raise HTTPException(status_code=400, detail="User already in server")
    
    # Check if pending request exists
    pending = db.query(JoinRequest).filter(JoinRequest.server_id == request.server_id, JoinRequest.user_id == current_user.id, JoinRequest.status == "pending").first()
    if pending:
        raise HTTPException(status_code=400, detail="Join request already pending")
    
    new_request = JoinRequest(user_id=current_user.id, server_id=request.server_id)
    db.add(new_request)
    db.commit()
    db.refresh(new_request)
    return new_request

@router.get("/join_requests/{server_id}", response_model=list[JoinRequestOut])
def get_join_requests(server_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    server = db.query(Server).filter(Server.id == server_id).first()
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")
    
    if server.admin_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    requests = db.query(JoinRequest).filter(JoinRequest.server_id == server_id, JoinRequest.status == "pending").all()
    return requests

@router.put("/join_requests/{request_id}", response_model=JoinRequestOut)
def update_join_request(request_id: str, update: JoinRequestUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    request = db.query(JoinRequest).filter(JoinRequest.id == request_id).first()
    if not request:
        raise HTTPException(status_code=404, detail="Request not found")
    
    server = db.query(Server).filter(Server.id == request.server_id).first()
    if server.admin_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    if update.status not in ["accepted", "declined"]:
        raise HTTPException(status_code=400, detail="Invalid status")
    
    request.status = update.status
    if update.status == "accepted":
        # Add to server_users
        server_user = ServerUser(server_id=request.server_id, user_id=request.user_id)
        db.add(server_user)
    
    db.commit()
    db.refresh(request)
    return request