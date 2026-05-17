import asyncio
import redis.asyncio as aioredis

async def test():
    r = await aioredis.from_url('redis://127.0.0.1:6379/0', encoding='utf-8', decode_responses=True)
    keys = await r.keys('chc:*')
    print('All CHC keys:', keys)
    await r.aclose()

asyncio.run(test())
