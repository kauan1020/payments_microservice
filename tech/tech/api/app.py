from http import HTTPStatus

from fastapi import FastAPI

from tech.api import  payments_router
from tech.interfaces.schemas.message_schema import (
    Message,
)


app = FastAPI()

app.include_router(payments_router.router, prefix='/payments', tags=['payments'])



@app.get('/', status_code=HTTPStatus.OK, response_model=Message)
def read_root():
    return {'message': 'Tech Challenge FIAP - Kauan Silva!  Payments Microservice'}
