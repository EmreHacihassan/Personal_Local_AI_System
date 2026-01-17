import asyncio
from core.llm_manager import llm_manager

async def test():
    print('Testing async streaming...')
    count = 0
    async for token in llm_manager.generate_stream_async('Merhaba'):
        print(token, end='', flush=True)
        count += 1
    print(f'\nDone, got {count} tokens')

asyncio.run(test())
