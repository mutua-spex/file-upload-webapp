import os
from datetime import timedelta
from typing import List

from fastapi import Depends, FastAPI, File, HTTPException, UploadFile, WebSocket, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlmodel import Session, select

from . import auth, chat, database, models, schemas

# Ensure upload folder exists
UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "static", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

app = FastAPI(title="ChatApp Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=os.path.join(os.path.dirname(__file__), "static")), name="static")


@app.on_event("startup")
async def startup_event() -> None:
    database.init_db()


@app.post("/api/auth/register", response_model=schemas.UserRead)
def register(user_in: schemas.UserCreate) -> schemas.UserRead:
    with database.get_session() as session:
        existing = auth.get_user_by_username(session, user_in.username)
        if existing:
            raise HTTPException(status_code=400, detail="Username already taken")

        user = models.User(
            username=user_in.username,
            hashed_password=auth.get_password_hash(user_in.password),
        )
        session.add(user)
        session.commit()
        session.refresh(user)
        return user


@app.post("/api/auth/token", response_model=schemas.Token)
def login_for_access_token(form_data: schemas.UserCreate) -> schemas.Token:
    with database.get_session() as session:
        user = auth.authenticate_user(session, form_data.username, form_data.password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = auth.create_access_token(
            data={"sub": user.username}, expires_delta=access_token_expires
        )
        refresh_token = auth.create_refresh_token(session, user)
        return schemas.Token(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=auth.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )


@app.post("/api/auth/refresh", response_model=schemas.Token)
def refresh_access_token(token_req: schemas.RefreshTokenRequest) -> schemas.Token:
    with database.get_session() as session:
        user = auth.refresh_user_from_token(session, token_req.refresh_token)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token",
            )

        # rotate refresh token
        auth.revoke_refresh_token(session, token_req.refresh_token)
        access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = auth.create_access_token(
            data={"sub": user.username}, expires_delta=access_token_expires
        )
        refresh_token = auth.create_refresh_token(session, user)
        return schemas.Token(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=auth.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )


@app.get("/api/me", response_model=schemas.UserRead)
def read_current_user(current_user: models.User = Depends(auth.get_current_user)) -> models.User:
    return current_user


@app.post("/api/rooms", response_model=schemas.RoomRead)
def create_room(room_in: schemas.RoomCreate, current_user: models.User = Depends(auth.get_current_user)) -> models.Room:
    with database.get_session() as session:
        existing = session.exec(select(models.Room).where(models.Room.name == room_in.name)).first()
        if existing:
            raise HTTPException(status_code=400, detail="Room already exists")
        room = models.Room(name=room_in.name, description=room_in.description)
        session.add(room)
        session.commit()
        session.refresh(room)
        return room


@app.get("/api/rooms", response_model=List[schemas.RoomRead])
def list_rooms() -> List[models.Room]:
    with database.get_session() as session:
        rooms = session.exec(select(models.Room)).all()
        return rooms


@app.get("/api/rooms/{room_id}/presence")
def get_room_presence(room_id: int) -> List[dict]:
    return chat.manager.get_room_users(str(room_id))


@app.get("/api/rooms/{room_id}/messages", response_model=List[schemas.MessageRead])
def get_room_messages(room_id: int, limit: int = 100) -> List[models.Message]:
    with database.get_session() as session:
        statement = (
            select(models.Message)
            .where(models.Message.room_id == room_id)
            .order_by(models.Message.created_at)
            .limit(limit)
        )
        return session.exec(statement).all()


@app.post("/api/upload")
def upload_file(
    file: UploadFile = File(...), current_user: models.User = Depends(auth.get_current_user)
) -> dict:
    filename = file.filename.replace(" ", "_")
    save_path = os.path.join(UPLOAD_DIR, filename)

    # ensure unique filename
    base, ext = os.path.splitext(filename)
    counter = 0
    while os.path.exists(save_path):
        counter += 1
        filename = f"{base}_{counter}{ext}"
        save_path = os.path.join(UPLOAD_DIR, filename)

    with open(save_path, "wb") as f:
        f.write(file.file.read())

    return {"url": f"/static/uploads/{filename}"}


@app.websocket("/ws/{room_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: int, token: str = None):
    # Token can be passed via query string: /ws/1?token=...
    if token is None:
        token = websocket.query_params.get("token")

    if not token:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    try:
        user = auth.get_user_from_token(token)
    except Exception:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await chat.manager.connect(str(room_id), websocket, user.id, user.username)
    await chat.manager.broadcast(
        str(room_id),
        {
            "type": "user_joined",
            "user": {"id": user.id, "username": user.username},
            "room_id": room_id,
            "presence": chat.manager.get_room_users(str(room_id)),
        },
    )

    try:
        while True:
            data = await websocket.receive_json()
            content = data.get("content")
            attachment_url = data.get("attachment_url")

            # Persist message
            with database.get_session() as session:
                message = models.Message(
                    room_id=room_id,
                    sender_id=user.id,
                    content=content,
                    attachment_url=attachment_url,
                )
                session.add(message)
                session.commit()
                session.refresh(message)

            await chat.manager.broadcast(
                str(room_id),
                {
                    "type": "message",
                    "message": {
                        "id": message.id,
                        "room_id": message.room_id,
                        "sender_id": message.sender_id,
                        "content": message.content,
                        "attachment_url": message.attachment_url,
                        "created_at": message.created_at.isoformat(),
                    },
                },
            )
    except WebSocketDisconnect:
        chat.manager.disconnect(str(room_id), websocket)
        await chat.manager.broadcast(
            str(room_id),
            {
                "type": "user_left",
                "user": {"id": user.id, "username": user.username},
                "room_id": room_id,
                "presence": chat.manager.get_room_users(str(room_id)),
            },
        )
