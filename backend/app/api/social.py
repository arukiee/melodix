from typing import List
from uuid import UUID
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.social import FriendRequest, Friendship
from app.schemas.social import (
    UserSummary,
    FriendRequestResponse,
    FriendshipResponse,
    PendingRequestsList
)

router = APIRouter(prefix="/social", tags=["social"])

@router.get("/friends", response_model=List[FriendshipResponse])
def list_friends(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    friendships = db.query(Friendship).filter(Friendship.user_id == current_user.id).all()
    return friendships

@router.get("/friends/requests", response_model=PendingRequestsList)
def list_friend_requests(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    incoming = db.query(FriendRequest).filter(
        and_(FriendRequest.receiver_id == current_user.id, FriendRequest.status == "PENDING")
    ).all()
    
    outgoing = db.query(FriendRequest).filter(
        and_(FriendRequest.sender_id == current_user.id, FriendRequest.status == "PENDING")
    ).all()

    return {
        "incoming": incoming,
        "outgoing": outgoing
    }

@router.get("/friends/search", response_model=List[UserSummary])
def search_users(
    q: str = "",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query_str = q.strip()
    if not query_str:
        return []

    # Get IDs of existing friends
    existing_friend_ids = [
        f.friend_id for f in db.query(Friendship.friend_id).filter(Friendship.user_id == current_user.id).all()
    ]
    
    # Get IDs of users with pending requests
    pending_sender_ids = [
        r.sender_id for r in db.query(FriendRequest.sender_id).filter(
            and_(FriendRequest.receiver_id == current_user.id, FriendRequest.status == "PENDING")
        ).all()
    ]
    pending_receiver_ids = [
        r.receiver_id for r in db.query(FriendRequest.receiver_id).filter(
            and_(FriendRequest.sender_id == current_user.id, FriendRequest.status == "PENDING")
        ).all()
    ]

    excluded_ids = set([current_user.id] + existing_friend_ids + pending_sender_ids + pending_receiver_ids)

    users = db.query(User).filter(
        and_(
            User.is_active == True,
            User.id.notin_(excluded_ids),
            or_(
                User.full_name.ilike(f"%{query_str}%"),
                User.email.ilike(f"%{query_str}%")
            )
        )
    ).limit(20).all()

    return users

@router.post("/friends/request/{target_user_id}", response_model=FriendRequestResponse)
def send_friend_request(
    target_user_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if target_user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot send friend request to yourself")

    target_user = db.query(User).filter(and_(User.id == target_user_id, User.is_active == True)).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")

    # Check existing friendship
    existing_friendship = db.query(Friendship).filter(
        and_(Friendship.user_id == current_user.id, Friendship.friend_id == target_user_id)
    ).first()
    if existing_friendship:
        raise HTTPException(status_code=400, detail="Already friends with this user")

    # Check pending request in either direction
    existing_request = db.query(FriendRequest).filter(
        or_(
            and_(FriendRequest.sender_id == current_user.id, FriendRequest.receiver_id == target_user_id, FriendRequest.status == "PENDING"),
            and_(FriendRequest.sender_id == target_user_id, FriendRequest.receiver_id == current_user.id, FriendRequest.status == "PENDING")
        )
    ).first()
    if existing_request:
        raise HTTPException(status_code=400, detail="A pending friend request already exists between these users")

    friend_req = FriendRequest(
        sender_id=current_user.id,
        receiver_id=target_user_id,
        status="PENDING"
    )
    db.add(friend_req)
    db.commit()
    db.refresh(friend_req)
    return friend_req

@router.post("/friends/accept/{request_id}", response_model=FriendshipResponse)
def accept_friend_request(
    request_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    req = db.query(FriendRequest).filter(
        and_(FriendRequest.id == request_id, FriendRequest.receiver_id == current_user.id, FriendRequest.status == "PENDING")
    ).first()
    if not req:
        raise HTTPException(status_code=404, detail="Friend request not found or already processed")

    req.status = "ACCEPTED"
    req.responded_at = datetime.utcnow()

    # Create dual friendship records
    f1 = Friendship(user_id=req.receiver_id, friend_id=req.sender_id)
    f2 = Friendship(user_id=req.sender_id, friend_id=req.receiver_id)
    db.add_all([f1, f2])
    
    db.commit()
    db.refresh(f1)
    return f1

@router.post("/friends/reject/{request_id}")
def reject_friend_request(
    request_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    req = db.query(FriendRequest).filter(
        and_(FriendRequest.id == request_id, FriendRequest.receiver_id == current_user.id, FriendRequest.status == "PENDING")
    ).first()
    if not req:
        raise HTTPException(status_code=404, detail="Friend request not found or already processed")

    req.status = "REJECTED"
    req.responded_at = datetime.utcnow()
    db.commit()
    return {"message": "Friend request rejected"}

@router.post("/friends/cancel/{request_id}")
def cancel_friend_request(
    request_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    req = db.query(FriendRequest).filter(
        and_(FriendRequest.id == request_id, FriendRequest.sender_id == current_user.id, FriendRequest.status == "PENDING")
    ).first()
    if not req:
        raise HTTPException(status_code=404, detail="Friend request not found or already processed")

    req.status = "CANCELLED"
    req.responded_at = datetime.utcnow()
    db.commit()
    return {"message": "Friend request cancelled"}

@router.delete("/friends/{friend_id}")
def remove_friend(
    friend_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    f1 = db.query(Friendship).filter(and_(Friendship.user_id == current_user.id, Friendship.friend_id == friend_id)).first()
    f2 = db.query(Friendship).filter(and_(Friendship.user_id == friend_id, Friendship.friend_id == current_user.id)).first()

    if not f1 and not f2:
        raise HTTPException(status_code=404, detail="Friendship not found")

    if f1:
        db.delete(f1)
    if f2:
        db.delete(f2)

    db.commit()
    return {"message": "Friend removed successfully"}
