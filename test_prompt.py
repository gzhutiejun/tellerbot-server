
from helper import serialize_json_object
from main import extract

import asyncio

schema = serialize_json_object({
    "schema": {
        "currency": "",
        "amount": 0,
        "cancel": False,
        "account": "",
        "term": "",
        "question": "",
    }
})


async def main():
    # case 1
    # res = await extract({
    #     "instruction": "Extract the currency, amount, cancel, account and term from the text",
    #     "text": "I want to withdraw 1000 dollars from my check account",
    #     "schema": schema,
    #     "language": "en"
    # })

    # case 2
    res = await extract({
        "instruction": '''Extract the currency, amount, cancel, account and term from the text. 
        If amount and currency are found, but account is not found, set question to "please tell what account do you want to use"
        ''',
        "text": "I want to withdraw 1000 dollars",
        "schema": schema,
        "language": "en"
    })

    # case 3
    # res = await extract({
    #     "instruction": '''Extract the currency, amount, cancel, account and term from the text. 
    #     if account is found, amount is 0 and currency is empty, set question to "please tell how much do you want to withdraw?"
    #     ''',
    #     "text": "savings account",
    #     "schema": schema,
    #     "language": "en"
    # })
    print(res["data"])

asyncio.run(main())