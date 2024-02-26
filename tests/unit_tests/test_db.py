import pytest

from users.db_queries import get_user_by_user_id, get_user_by_username


@pytest.mark.parametrize(('user_id, username, is_exists'),
                         [(1, 'user1',True),
                          (2, 'user2', True),
                          (4, 'user4', False)])
async def test_get_user_by_user_id(user_id, username, is_exists):
    user = await get_user_by_user_id(user_id)

    if is_exists:
        assert user.id == user_id
        assert user.username == username
    else:
        assert not user


@pytest.mark.parametrize(('user_id, username, is_exists'),
                         [(1, 'user1',True),
                          (2, 'user2', True),
                          (4, 'user4', False)])
async def test_get_user_by_username(user_id, username, is_exists):
    user = await get_user_by_username(username)

    if is_exists:
        assert user.id == user_id
        assert user.username == username
    else:
        assert not user