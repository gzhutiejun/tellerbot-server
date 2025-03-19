from pydantic import BaseModel

class SessionModel(BaseModel): 
    transaction: str
    cancel: bool

class AmountAccountModel(BaseModel):
    currency: str
    amount: float
    account: str
    cancel: bool

class AmountModel(BaseModel):
    currency: str
    amount: float
    cancel: bool

class ResultModel(BaseModel):
    answer: bool
    cancel: bool

