from fastapi import HTTPException, status


def raise_unauthorized_error():
    raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail={'status': 'error',
                                                              'message': 'Failed access to the bybit API. Please update your keys'})


def raise_conflict_error(message):
    raise HTTPException(status.HTTP_409_CONFLICT, detail={'status': 'error', 'message': message})