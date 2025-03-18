from pydantic import BaseModel
class TransactionModel(BaseModel):
    currency: str
    amount: float
    account: str

class SessionModel(BaseModel): 
    transaction: str
    cancelled: bool