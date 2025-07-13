import pytest
import asyncio
from redis_client import add_key_value_redis, get_value_redis, delete_key_redis

@pytest.mark.asyncio
async def test_redis_set_get_delete():
    await add_key_value_redis("testkey", "testvalue", expire=5)
    value = await get_value_redis("testkey")
    assert value.decode() == "testvalue"

    await delete_key_redis("testkey")
    value = await get_value_redis("testkey")
    assert value is None
