from app.services.agentic.agentic_job_search import start_job_search, process_job_search_response
import asyncio

async def test_flow():
    # 1. 검색 시작
    print('\n=== 검색 시작 ===')
    state = await start_job_search('test_user')
    print(f'검색 상태: {state}')
    
    # 2. 긍정 응답 처리
    print('\n=== 긍정 응답 처리 ===')
    result = await process_job_search_response('네, 백엔드 개발자로 일하고 싶어요')
    print(f'응답 상태: {result["status"]}')
    print(f'응답 메시지: {result["message"]}')
    
    if 'results' in result:
        print('\n=== 검색 결과 ===')
        for item in result['results']:
            print(f'\n제목: {item["title"]}')
            print(f'링크: {item["link"]}')
            print(f'설명: {item["snippet"]}')

if __name__ == '__main__':
    asyncio.run(test_flow()) 