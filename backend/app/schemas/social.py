from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict
from uuid import UUID

class UserSummary(BaseModel):
    id: UUID
    full_name: str
    email: str
    avatar_url: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class FriendRequestResponse(BaseModel):
    id: UUID
    sender_id: UUID
    receiver_id: UUID
    status: str
    created_at: datetime
    sender: UserSummary
    receiver: UserSummary

    model_config = ConfigDict(from_attributes=True)

class FriendshipResponse(BaseModel):
    id: UUID
    user_id: UUID
    friend_id: UUID
    created_at: datetime
    friend: UserSummary

    model_config = ConfigDict(from_attributes=True)

class PendingRequestsList(BaseModel):
    incoming: List[FriendRequestResponse]
    outgoing: List[FriendRequestResponse]
