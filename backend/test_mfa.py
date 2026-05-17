import asyncio
import sys
sys.path.insert(0, '.')
from app.services.otp_service import mfa_session_create, mfa_session_get

async def test():
    token = await mfa_session_create('test@test.com', 'fake_session_123')
    print('Token created:', token[:20])
    data = await mfa_session_get(token)
    print('Data retrieved:', data)

asyncio.run(test())
