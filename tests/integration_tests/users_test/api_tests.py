from httpx import AsyncClient
import pytest

from config import settings


@pytest.mark.parametrize('email, password, status_code',[(settings.TEST_USERNAME, settings.TEST_USERNAME, 200),
                                                         ('original', '12345678', 409),
                                                         ('original1', '12345678', 200),
                                                         ('', '12345678', 422),
                                                         ('original12', '', 422),
                                                         ('', '12345678', 422),
                                                         ('', '', 422),
                                                         ])
async def test_register_user(ac: AsyncClient, email, password, status_code):
    response = await ac.post('/api/register', json={
                                        "username": email,
                                        "password": password
                                            })
    assert response.status_code == status_code


@pytest.mark.parametrize('email, password, status_code',[(settings.TEST_USERNAME, settings.TEST_USERNAME, 200),
                                                         ('original2', '12345678', 401),
                                                         ('original', '123456783', 401),
                                                         ('', '12345678', 422),
                                                         ('original12', '', 422),
                                                         ('', '12345678', 422),
                                                         ('', '', 422),
                                                         ])
async def test_create_token(ac: AsyncClient, email, password, status_code):
    response = await ac.post('/api/tokens', json={
                                        "username": email,
                                        "password": password
                                            })
    assert response.status_code == status_code

async def get_token(ac: AsyncClient):
    response = await ac.post('/api/tokens', json={
        "username": settings.TEST_USERNAME,
        "password": settings.TEST_USERNAME
    })
    assert response.status_code == 200

    token = response.json().get('token')
    return token



async def test_update_keys_valid_token(ac: AsyncClient):
    token = await get_token(ac)
    response = await ac.put(
        "/api/keys",
        headers={'token': token},
        json={
            "api_key": "MyTestApiKey",
            "api_secret": "MyTestApiSecret",
        },
    )

    assert response.status_code == 200

@pytest.mark.parametrize('api_key, api_secret, status_code',
                         [(settings.TEST_EXCHANGE_API_SECRET, settings.TEST_EXCHANGE_API_SECRET, 200),
                          ('1234', settings.TEST_EXCHANGE_API_SECRET, 401),
                          (settings.TEST_EXCHANGE_API_SECRET, '1234', 401),
                          ('', '', 422),
                          ('', 'adf', 422),
                          ('adff', '', 422),
                          ])
async def test_update_keys_invalid_token(ac: AsyncClient, api_key, api_secret, status_code):
    response = await ac.put(
        "/api/keys",
        headers={'token': 'wrong_token'},
        json={
            "api_key": api_key,
            "api_secret": api_secret,
        },
    )

    assert response.status_code == 401

@pytest.mark.parametrize('coin1, coin2, status_code',[('BTC', 'USD', 200),
                                                      ('BTC,ETH','USD,EUR', 200),
                                                      ('BTC,ETH', 'USD', 200),
                                                      ('coin1', 'USD', 409),
                                                      ('', 'USD', 409),
                                                      ('', '', 409),
                                                      ('', 'USD', 409),])
async def test_exchanges(ac: AsyncClient, coin1, coin2, status_code):
    token = await get_token(ac)
    response = await ac.get(
        f"/api/prices?coins_from={coin1}&coins_to={coin2}",
        headers={'token': token},
    )

    assert response.status_code == status_code


@pytest.mark.parametrize('api_key, api_secret, status_code',
                         [(settings.TEST_EXCHANGE_API_KEY, settings.TEST_EXCHANGE_API_SECRET, 200),
                          ('1234', settings.TEST_EXCHANGE_API_SECRET, 401),
                          (settings.TEST_EXCHANGE_API_SECRET, '1234', 401),
                          ])
async def test_positions(ac: AsyncClient, api_key, api_secret, status_code):
    token = await get_token(ac)

    await ac.put(
        "/api/keys",
        headers={'token': token},
        json={
            "api_key": api_key,
            "api_secret": api_secret,
        },
    )

    response = await ac.get(
        f"/api/positions",
        headers={'token': token},
    )

    assert response.status_code == status_code


@pytest.mark.parametrize('symbol, status_code',[('ADAUSDT', 200),
                                                ('asdf', 409),
                                                      ])
async def test_exchanges(ac: AsyncClient, symbol, status_code):
    token = await get_token(ac)

    await ac.put(
        "/api/keys",
        headers={'token': token},
        json={
            "api_key": settings.TEST_EXCHANGE_API_KEY,
            "api_secret": settings.TEST_EXCHANGE_API_SECRET,
        },
    )

    response = await ac.get(
        f"/api/position?symbol={symbol}",
        headers={'token': token},
    )
    print(response)

    assert response.status_code == status_code

