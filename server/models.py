from pydantic import BaseModel
from typing import Any


class RegisterReq(BaseModel):
    voter_id: str
    h: str  


class CastReq(BaseModel):
    voter_id: str
    h: str
    enc_vote: Any  
    signed_ballot: Any  

