import os
from loguru import logger
from playwright.async_api import async_playwright

class UserPDF:
    def __init__(self):
        os.makedirs("output", exist_ok=True)

    async def make_pdf(self, uid: str, html: str) -> str:
        output_path = f"output/{uid}_resume.pdf"

        async with async_playwright() as p:
            # EKS 환경에 맞는 브라우저 실행 옵션 설정
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-gpu',
                    '--disable-background-timer-throttling',
                    '--disable-backgrounding-occluded-windows',
                    '--disable-renderer-backgrounding',
                    '--disable-features=TranslateUI',
                    '--disable-web-security',
                    '--disable-features=VizDisplayCompositor',
                    '--disable-extensions',
                    '--no-first-run',
                    '--disable-default-apps'
                ]
            )
            page = await browser.new_page()
            
            # HTML 문자열 직접 렌더링
            await page.set_content(html, wait_until="load")
            
            # PDF로 저장
            await page.pdf(
                path=output_path,
                format="A4",
                margin={"top": "20mm", "bottom": "20mm", "left": "20mm", "right": "20mm"},
                print_background=True  # 배경색/이미지 포함
            )

            await browser.close()

        logger.info(f"✅ PDF 생성 완료: {output_path}")
        return output_path

    async def delete_pdf(self, uid: str):
        path = f"output/{uid}_resume.pdf"
        if os.path.exists(path):
            os.remove(path)
            logger.info(f"🗑️ PDF 삭제 완료: {path}")
        else:
            logger.warning(f"⚠️ 삭제하려는 PDF가 존재하지 않음: {path}")


    async def pdf_html_form(self, user_data: dict):
        logger.info(f"[html_form 변환중인데이터] : {user_data}")
        html_form = f"""
        <!DOCTYPE html>
        <html lang="ko">
        <head>
        <meta charset="UTF-8">
        <title>이력서</title>
        <style>
        @page {{
            size: A4;
            margin: 0;
        }}
        body {{
            font-family: "Batang", serif;
            margin: 0;
            padding: 0;
            line-height: 1.6;
            font-size: 12px;
        }}
        .resume-page {{
            width: 210mm;
            height: 297mm;
            padding: 20mm 20mm 25mm 20mm;
            box-sizing: border-box;
            background: white;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 18px;
        }}
        th, td {{
            border: 1px solid black;
            padding: 8px;
            text-align: center;
            vertical-align: middle;
            height: 20px;
        }}
        .photo-cell {{
            width: 30mm;
            height: 40mm;
            font-size: 10px;
            color: #666;
        }}
        .title-cell {{
            font-size: 24px;
            letter-spacing: 12px;
            font-weight: bold;
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
            text-align: center;
            font-size: 12px;
            margin-top: 50px;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
        }}
        .date-line {{
            margin: 25px 0;
            line-height: 1.8;
        }}
        </style>
        </head>
        <body>
        <div class="resume-page">
            <table>
            <tr>
                <td rowspan="3" class="photo-cell">(사 진)</td>
                <td colspan="6" class="title-cell">이 력 서</td>
            </tr>
            <tr>
                <td>성 명</td>
                <td colspan="2">{user_data.get('name', '')}</td>
                <td colspan="2">생년월일</td>
                <td>{user_data.get('birth', '')}</td>
            </tr>
            <tr>
                <td>전화번호</td>
                <td colspan="2">{user_data.get('phone', '')}</td>
                <td colspan="2">국적</td>
                <td>{user_data.get('nationality', '')}</td>
            </tr>
            <tr>
                <td rowspan="4">가족관계</td>
                <td>관 계</td>
                <td>성 명</td>
                <td colspan="2">연 령</td>
                <td colspan="2">현재직업</td>
            </tr>
            <tr>
                <td>{user_data.get('relation1', '')}</td>
                <td>{user_data.get('name1', '')}</td>
                <td colspan="2">{user_data.get('age1', '')}</td>
                <td colspan="2">{user_data.get('job1', '')}</td>
            </tr>
            <tr>
                <td>{user_data.get('relation2', '')}</td>
                <td>{user_data.get('name2', '')}</td>
                <td colspan="2">{user_data.get('age2', '')}</td>
                <td colspan="2">{user_data.get('job2', '')}</td>
            </tr>
            <tr>
                <td>{user_data.get('relation3', '')}</td>
                <td>{user_data.get('name3', '')}</td>
                <td colspan="2">{user_data.get('age3', '')}</td>
                <td colspan="2">{user_data.get('job3', '')}</td>
            </tr>
            <tr>
                <td colspan="2">현 주 소</td>
                <td colspan="5">{user_data.get('address', '')}</td>
            </tr>
            <tr>
                <td colspan="2">이메일</td>
                <td colspan="5">{user_data.get('email', '')}</td>
            </tr>
            </table>

            <table>
            <thead>
                <tr>
                <th class="period-cell">기 간</th>
                <th class="content-cell">학 력 · 자 격 사 항</th>
                <th class="note-cell">비 고</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                <td>{user_data.get('edu_period1', '')}</td>
                <td>{user_data.get('edu_detail1', '')}</td>
                <td></td>
                </tr>
                <tr>
                <td>{user_data.get('edu_period2', '')}</td>
                <td>{user_data.get('edu_detail2', '')}</td>
                <td></td>
                </tr>
                 <tr>
                <td>{user_data.get('edu_period3', '')}</td>
                <td>{user_data.get('edu_detail3', '')}</td>
                <td></td>
                </tr>
                 <tr>
                <td>{user_data.get('edu_period4', '')}</td>
                <td>{user_data.get('edu_detail4', '')}</td>
                <td></td>
                </tr>
            </tbody>
            </table>

            <table>
            <thead>
                <tr>
                <th class="period-cell">기 간</th>
                <th class="content-cell">경 력 사 항</th>
                <th class="note-cell">비 고</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                <td>{user_data.get('career_period1', '')}</td>
                <td>{user_data.get('career_detail1', '')}</td>
                <td>{user_data.get('career_note1', '')}</td>
                </tr>
                <tr>
                <td>{user_data.get('career_period2', '')}</td>
                <td>{user_data.get('career_detail2', '')}</td>
                <td>{user_data.get('career_note2', '')}</td>
                </tr>   
                <tr>
                <td>{user_data.get('career_period3', '')}</td>
                <td>{user_data.get('career_detail3', '')}</td>
                <td>{user_data.get('career_note3', '')}</td>
                </tr>       
                <tr>
                <td>{user_data.get('career_period4', '')}</td>
                <td>{user_data.get('career_detail4', '')}</td>
                <td>{user_data.get('career_note4', '')}</td>
                </tr>       
            </tbody>
            </table>

            <div class="footer">
            <p>위의 기재한 내용이 사실과 다름이 없습니다.</p>
            <div class="date-line">{user_data.get('written_date', '')}</div>
            <p>{user_data.get('name', '')}(인)</p>
            </div>
        </div>
        </body>
        </html>
        """
        return html_form

