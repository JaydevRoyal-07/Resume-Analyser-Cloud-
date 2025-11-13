import os
from fastapi import APIRouter, HTTPException, UploadFile, File, Header
from .config import settings
from .auth import hash_password, verify_password, create_token, decode_token
from pymongo import MongoClient
from bson.objectid import ObjectId
import requests
from typing import Optional

router = APIRouter()
client = MongoClient(settings.MONGO_URI)
db = client.get_default_database()
users = db.users
candidates = db.candidates

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

def get_user_from_auth(authorization: Optional[str]):
    if not authorization:
        return None
    parts = authorization.split()
    if len(parts) != 2:
        return None
    token = parts[1]
    payload = decode_token(token)
    return payload

@router.post("/auth/register")
def register(payload: dict):
    name = payload.get("name")
    email = payload.get("email")
    password = payload.get("password")
    role = payload.get("role", "hr")
    if not (name and email and password):
        raise HTTPException(status_code=400, detail="Missing fields")
    if users.find_one({"email": email}):
        raise HTTPException(status_code=400, detail="User exists")
    ph = hash_password(password)
    res = users.insert_one({"name": name, "email": email, "passwordHash": ph, "role": role})
    return {"id": str(res.inserted_id), "email": email}

@router.post("/auth/login")
def login(payload: dict):
    email = payload.get("email")
    password = payload.get("password")
    u = users.find_one({"email": email})
    if not u or not verify_password(password, u["passwordHash"]):
        raise HTTPException(status_code=400, detail="Invalid credentials")
    token = create_token({"id": str(u["_id"]), "email": u["email"], "role": u.get("role", "hr")})
    return {"token": token, "user": {"id": str(u["_id"]), "email": u["email"], "name": u["name"], "role": u.get("role","hr")}}

@router.post("/resume/upload")
def upload_resume(authorization: Optional[str] = Header(None), file: UploadFile = File(...)):
    user = get_user_from_auth(authorization)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    # save file
    filename = f"{int(__import__('time').time()*1000)}-{file.filename}"
    path = os.path.join(UPLOAD_DIR, filename)
    with open(path, "wb") as f:
        f.write(file.file.read())
    # send to ml analyzer
    try:
        files = {"file": open(path, "rb")}
        resp = requests.post(settings.ML_ANALYZER_URL, files=files, timeout=120)
        analysis = resp.json()
    except Exception as e:
        analysis = {"error": "ML analyzer failed", "detail": str(e)}
    score = analysis.get("score") if isinstance(analysis, dict) else 0
    cand = {
        "filename": filename,
        "originalName": file.filename,
        "uploader": user["id"],
        "analysis": analysis,
        "score": score
    }
    res = candidates.insert_one(cand)
    cand["_id"] = str(res.inserted_id)
    return cand

@router.get("/resume/candidates")
def list_candidates(authorization: Optional[str] = Header(None)):
    user = get_user_from_auth(authorization)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    docs = []
    for d in candidates.find().sort("createdAt", -1):
        d["id"] = str(d["_id"])
        d["_id"] = str(d["_id"])
        docs.append(d)
    return docs

@router.get("/resume/{cid}")
def get_candidate(cid: str, authorization: Optional[str] = Header(None)):
    user = get_user_from_auth(authorization)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    d = candidates.find_one({"_id": ObjectId(cid)})
    if not d:
        raise HTTPException(status_code=404, detail="Not found")
    d["_id"] = str(d["_id"])
    return d
