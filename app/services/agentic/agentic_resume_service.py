import os
import tempfile
from typing import Dict
import asyncio
from playwright.async_api import async_playwright
from app.core.llm_client import get_llm_client
from loguru import logger

# 이력서 생성 프롬프트
def generate_resume_prompt(user_data: Dict[str, str]) -> str:
    return f"""
    다음은 사용자의 이력서 정보입니다.

    [이름] {user_data.get('name', '')}
    [직업] {user_data.get('job_title', '')}
    [경력] {user_data.get('experience', '')}
    [기술] {user_data.get('skills', '')}
    [학력] {user_data.get('education', '')}

    위 정보를 바탕으로 전문적이고 매력적인 이력서를 작성해주세요.
    응답은 명확하고 구체적이어야 합니다.
    """

async def generate_resume_text(user_data: Dict[str, str], max_retries: int = 3) -> str:
    last_error = None
    
    for attempt in range(max_retries):
        try:
            client = get_llm_client(is_lightweight=True)
            prompt = generate_resume_prompt(user_data)
            
            logger.info(f"📤 LLM 요청 프롬프트 (시도 {attempt + 1}/{max_retries}):\n{prompt}")
            
            resume_text = await client.generate(prompt)
            
            if not resume_text or not resume_text.strip():
                raise ValueError("LLM 응답이 비어있습니다.")
                
            logger.info(f"📥 LLM 응답 성공 (처음 500자):\n{resume_text[:500]}...")
            return resume_text
            
        except Exception as e:
            last_error = e
            logger.error(f"🚨 이력서 텍스트 생성 실패 (시도 {attempt + 1}/{max_retries}): {str(e)}", exc_info=True)
            
            if attempt < max_retries - 1:
                wait_time = (attempt + 1) * 2  # 지수 백오프: 2초, 4초, 6초...
                logger.info(f"⏳ {wait_time}초 후 재시도합니다...")
                await asyncio.sleep(wait_time)
            else:
                logger.error(f"❌ 최대 재시도 횟수 ({max_retries}회) 도달")
                raise ValueError(f"이력서 텍스트 생성 실패 ({max_retries}회 시도): {str(last_error)}")

async def save_resume_pdf(user_data: Dict[str, str], resume_text: str) -> str:
    html_path = None
    browser = None
    
    try:
        # 경력사항과 학력사항을 줄바꿈으로 분리
        experience_items = user_data.get('experience', '').split('\n')
        education_items = user_data.get('education', '').split('\n')
        
        content_html = resume_text.replace("\n", "<br>")
        html = f"""
        <!DOCTYPE html>
        <html lang="ko">
        <head>
            <meta charset="UTF-8">
            <style>
                @page {{
                    size: A4;
                    margin: 0;
                }}
                body {{
                    font-family: 'Batang', serif;
                    margin: 0;
                    padding: 0;
                    line-height: 1.5;
                }}
                .page {{
                    width: 210mm;
                    height: 297mm;
                    padding: 15mm 20mm;
                    box-sizing: border-box;
                }}
                h1 {{
                    text-align: center;
                    font-size: 24px;
                    margin-bottom: 10px;
                    letter-spacing: 15px;
                    font-weight: normal;
                }}
                table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin-bottom: 20px;
                    font-size: 11px;
                }}
                th, td {{
                    border: 1.2px solid black;
                    padding: 8px 4px;
                    text-align: center;
                    vertical-align: middle;
                    height: 25px;
                    box-sizing: border-box;
                }}
                .photo-cell {{
                    width: 30mm;
                    height: 40mm;
                    text-align: center;
                    vertical-align: middle;
                    font-size: 10px;
                    color: #666;
                }}
                .header-table td {{
                    height: 32px;
                }}
            
                .family-table td {{
                    height: 28px;
                }}
                .period-cell {{
                    width: 20%;
                }}
                .content-cell {{
                    width: 60%;
                }}
                .note-cell {{
                    width: 20%;
                }}
                .footer {{
                    margin-top: 60px;
                    text-align: center;
                    font-size: 12px;
                }}
                .date-line {{
                    margin: 30px 0;
                    line-height: 2;
                }}
            </style>
        </head>
        <body>
            <div class="page">
                <table class="header-table">
                    <tr>
                        <td rowspan="3" class="photo-cell">(사 진)</td>
                        <td colspan="6"><h1>이 력 서</h1></td>
                    </tr>
                    <tr>
                        <td>성 명</td>
                        <td colspan="2">{user_data.get('name', '')}</td>
                        <td colspan="2">생년월일</td>
                        <td colspan="2"></td>
                    </tr>
                    <tr>
                        <td>전화번호</td>
                        <td colspan="2"></td>
                        <td colspan="2">국적</td>
                        <td ></td>
                    </tr>
                    <tr>
                    <td rowspan="4">가족관계</td>
                        <td>관 계</td>
                        <td>성 명</td>
                        <td colspan="2">연 령</td>
                        <td colspan="2">현재직업</td>
                    </tr>
                     <tr>
                        <td></td>
                        <td></td>
                        <td colspan="2"></td>
                        <td colspan="2"></td>
                    </tr>
                     <tr>
                        <td></td>
                        <td></td>
                        <td colspan="2"></td>
                        <td colspan="2"></td>
                    </tr>
                     <tr>
                        <td></td>
                        <td></td>
                        <td colspan="2"></td>
                        <td colspan="2"></td>
                    </tr>
                    <tr>
                        <td colspan="2">현 주 소</td>
                        <td colspan="5"></td>
                    </tr>
                    <tr>
                        <td colspan="2">이메일</td>
                        <td colspan="5"></td>
                    </tr>
                </table>

                <table>
                    <tr>
                        <th class="period-cell">기 간</th>
                        <th class="content-cell">학 력 · 병 역 · 자 격 사 항</th>
                        <th class="note-cell">비 고</th>
                    </tr>
                    <tr><td></td><td></td><td></td></tr>
                    <tr><td></td><td></td><td></td></tr>
                    <tr><td></td><td></td><td></td></tr>
                    <tr><td></td><td></td><td></td></tr>
                    <tr><td></td><td></td><td></td></tr>
                </table>

                <table>
                    <tr>
                        <th class="period-cell">기 간</th>
                        <th class="content-cell">경 력 사 항</th>
                        <th class="note-cell">비 고</th>
                    </tr>
                    <tr><td></td><td></td><td></td></tr>
                    <tr><td></td><td></td><td></td></tr>
                    <tr><td></td><td></td><td></td></tr>
                </table>

                <div class="footer">
                    <p>위의 기재한 내용이 사실과 다름이 없습니다.</p>
                    <div class="date-line">
                        20&nbsp;&nbsp;&nbsp;&nbsp;년&nbsp;&nbsp;&nbsp;&nbsp;월&nbsp;&nbsp;&nbsp;&nbsp;일
                    </div>
                    <p>(인)</p>
                </div>
            </div>
        </body>
        </html>"""

        # HTML 파일 생성
        with tempfile.NamedTemporaryFile(delete=False, suffix=".html", mode="w", encoding="utf-8") as f:
            html_path = f.name
            f.write(html)
            logger.info(f"📄 HTML 파일 생성: {html_path}")

        # PDF 파일 경로 설정
        pdf_path = f"{tempfile.gettempdir()}/{user_data['name']}_resume.pdf"
        
        # Playwright를 사용하여 PDF 생성
        async with async_playwright() as p:
            try:
                browser = await p.chromium.launch(
                    headless=True,
                    args=['--no-sandbox', '--disable-setuid-sandbox']
                )
                context = await browser.new_context()
                page = await context.new_page()
                
                # 파일 URL 로드
                file_url = f"file://{os.path.abspath(html_path)}"
                logger.info(f"🌐 HTML 파일 URL: {file_url}")
                await page.goto(file_url)
                
                # 페이지 로딩 완료 대기
                await page.wait_for_load_state('networkidle')
                await page.wait_for_load_state('domcontentloaded')
                
                # PDF 생성
                await page.pdf(
                    path=pdf_path,
                    format='A4',
                    margin={'top': '0', 'right': '0', 'bottom': '0', 'left': '0'},
                    print_background=True,
                    prefer_css_page_size=True
                )
                
                if not os.path.exists(pdf_path):
                    raise FileNotFoundError("PDF 파일이 생성되지 않았습니다.")
                
                file_size = os.path.getsize(pdf_path)
                logger.info(f"✅ PDF 파일 생성 완료: {pdf_path} (크기: {file_size} bytes)")
                
                return pdf_path
                
            except Exception as e:
                logger.error(f"🚨 Playwright 에러: {str(e)}")
                raise
            finally:
                if browser:
                    await browser.close()

    except Exception as e:
        logger.error(f"🚨 PDF 생성 실패: {str(e)}", exc_info=True)
        raise

    finally:
        # 임시 HTML 파일 정리
        if html_path and os.path.exists(html_path):
            try:
                os.remove(html_path)
                logger.info(f"🗑 임시 HTML 파일 삭제: {html_path}")
            except Exception as e:
                logger.warning(f"⚠️ 임시 HTML 파일 삭제 실패: {str(e)}")
                logger.warning(f"⚠️ 임시 HTML 파일 삭제 실패: {str(e)}")