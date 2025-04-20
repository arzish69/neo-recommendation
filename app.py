from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from firebase_admin import initialize_app, credentials, firestore, auth, _apps
from typing import List, Optional
from recommender import TopicBasedRecommender
from feed_manager import FeedManager

app = FastAPI()

origins = [
    "http://localhost:5173",
    "https://dorkmark.vercel.app",
    "https://dorkmark.com"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]  # Add this to expose any custom headers
)

if not _apps:
    cred = credentials.Certificate("service_acc.json")
    initialize_app(cred)

db = firestore.client()

recommender = TopicBasedRecommender()
feed_manager = FeedManager()

async def get_current_user(authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header missing")
    try:
        token = authorization.replace('Bearer ', '')
        decoded_token = auth.verify_id_token(token)
        uid = decoded_token['uid']

        # Fetch user interests from Firestore
        user_ref = db.collection('users').document(uid)
        user_data = user_ref.get()

        if not user_data.exists:
            raise HTTPException(status_code=404, detail="User not found")

        user_dict = user_data.to_dict()
        interests = user_dict.get("interests", [])
        nationality = user_dict.get("nationality", "US")  # Default to US if not provided

        return {"uid": uid, "interests": interests, "nationality": nationality}
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid authentication: {str(e)}")
    

@app.get("/api/recommendations")
async def get_recommendations(
    user_profile: str = "General interest reader",
    feed_urls: Optional[List[str]] = None,
    current_user: dict = Depends(get_current_user)
):
    if not feed_urls:
        feed_urls = feed_manager.get_feeds_for_user(
            current_user['interests'],
            current_user['nationality']
        )

    try:
        recommendations = await recommender.get_recommendations(
            user_profile,
            feed_urls,
            current_user['interests']
        )
        return {
            "recommendations": recommendations,
            "user_id": current_user['uid'],
            "interests": current_user['interests'],
            "nationality": current_user['nationality']
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.on_event("shutdown")
async def shutdown_event():
    await recommender.close()

@app.get("/")
async def root():
    return {"status": "ok"}