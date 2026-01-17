"""Test generator script."""
import asyncio
from core.study_document_generator import study_document_generator

async def test():
    print('Test basliyor...')
    try:
        async for event in study_document_generator.generate_document(
            document_id='54910547-4d06-4b1f-9dc3-f783b68d4ad0',
            active_source_ids=[],
            custom_instructions='',
            web_search='off'
        ):
            event_type = event.get('type', 'unknown')
            message = event.get('message', '')
            print(f'Event: {event_type} - {message}')
    except Exception as e:
        print(f'HATA: {e}')
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    asyncio.run(test())
