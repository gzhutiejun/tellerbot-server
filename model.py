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

def getJsonSchema(schema: str) -> dict[str, any]:
    match (schema):
        case "amountaccount":
            return AmountAccountModel.model_json_schema()
        case "amount":
            return AmountModel.model_json_schema()
        case "result":
            return ResultModel.model_json_schema()
        case _:
            return SessionModel.model_json_schema()