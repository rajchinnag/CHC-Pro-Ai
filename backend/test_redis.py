import asyncio
import redis.asyncio as aioredis

async def test():
    r = await aioredis.from_url('redis://127.0.0.1:6379/0', encoding='utf-8', decode_responses=True)
    token = 'test123'
    result = await r.setex(f'chc:mfa:{token}', 300, 'testvalue')
    print('Set result:', result)
    val = await r.get(f'chc:mfa:{token}')
    print('Get result:', val)
    keys = await r.keys('chc:mfa:*')
    print('All MFA keys:', keys)
    await r.aclose()

asyncio.run(test())
