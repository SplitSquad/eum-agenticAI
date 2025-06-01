import os
from datetime import datetime
from playwright.async_api import async_playwright
from loguru import logger
import re

class UserCoverLetterPDF:
    def __init__(self):
        os.makedirs("output_coverletter", exist_ok=True)

    async def make_pdf(self, uid: str, html: str) -> str:
        output_path = f"output_coverletter/{uid}_coverletter.pdf"
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
            await page.set_content(html, wait_until="load")
            await page.pdf(
                path=output_path,
                format="A4",
                margin={"top": "20mm", "bottom": "20mm", "left": "20mm", "right": "20mm"},
                print_background=True
            )
            await browser.close()
        logger.info(f"✅ [자소서] PDF 생성 완료: {output_path}")
        return output_path

    async def delete_pdf(self, uid: str):
        path = f"output_coverletter/{uid}_coverletter.pdf"
        if os.path.exists(path):
            os.remove(path)
            logger.info(f"🗑️ [자소서] PDF 삭제 완료: {path}")
        else:
            logger.warning(f"⚠️ [자소서] 삭제하려는 PDF가 존재하지 않음: {path}")

    def _clean_section_text(self, text: str) -> str:
        """문단 내 불필요한 줄바꿈, 중복 공백, 어색한 분리 등을 정제하여 자연스럽게 만듦"""
        # 여러 줄바꿈을 하나의 문단 구분(\n\n)으로 통일
        text = re.sub(r'\n{3,}', '\n\n', text)
        # 문장 중간의 불필요한 줄바꿈(문장 끝이 아닌 곳의 \n)을 공백으로 치환
        text = re.sub(r'(?<![.!?])\n(?!\n)', ' ', text)
        # 문장 끝(마침표, 물음표, 느낌표 등) 뒤에 붙은 \n은 문단 구분으로 유지
        text = re.sub(r'([.!?])\n', r'\1\n', text)
        # 중복 공백 제거
        text = re.sub(r' +', ' ', text)
        # 앞뒤 공백/줄바꿈 정리
        text = text.strip()
        return text

    def split_cover_letter_sections(self, cover_letter: str):
        """AI가 생성한 자기소개서를 4개 항목으로 분리 (정확한 번호와 제목 기준, 중복 없이, 불필요한 텍스트 제거 및 자연스러운 문단 정리)"""
        pattern = r"[\[]?1[\].]? ?성장 과정 및 가치관[\]]?(.*?)(?=\n?\[?2[\].]? ?지원 동기 및 포부[\]]?|\Z)" \
                  r"|\[?2[\].]? ?지원 동기 및 포부[\]]?(.*?)(?=\n?\[?3[\].]? ?역량 및 경험[\]]?|\Z)" \
                  r"|\[?3[\].]? ?역량 및 경험[\]]?(.*?)(?=\n?\[?4[\].]? ?입사 후 계획[\]]?|\Z)" \
                  r"|\[?4[\].]? ?입사 후 계획[\]]?(.*)"
        sections = [None, None, None, None]
        matches = list(re.finditer(pattern, cover_letter, re.DOTALL))
        for m in matches:
            for i in range(4):
                if m.group(i+1):
                    sections[i] = m.group(i+1).strip()
        # fallback: 문단 4등분
        if not all(sections):
            paras = [p.strip() for p in re.split(r'\n{2,}', cover_letter) if p.strip()]
            n = len(paras)
            chunk = max(1, n // 4)
            sections = ["\n\n".join(paras[i*chunk:(i+1)*chunk]) for i in range(4)]
            if n > chunk*4:
                sections[3] += "\n\n" + "\n\n".join(paras[chunk*4:])
        clean_sections = []
        for idx, sec in enumerate(sections):
            if not sec:
                clean_sections.append('')
                continue
            sec = re.sub(r'자기소개서', '', sec)
            sec = re.sub(r'\[.*?\]', '', sec)
            sec = re.sub(r'^[0-9]+\.? ?[가-힣 ]+', '', sec)
            sec = sec.strip()
            # 추가: 자연스러운 문단/공백/줄바꿈 정제
            sec = self._clean_section_text(sec)
            clean_sections.append(sec)
        return tuple(clean_sections)

    def pdf_html_form(self, cover_letter: str,user_name: str) -> str:
        """자기소개서 HTML 생성 (한 페이지에 여러 칸, 칸이 넘칠 때만 자동 페이지 분리, 불필요한 텍스트 제거 및 자연스러운 문단 정리)"""
        growth, motivation, experience, plan = self.split_cover_letter_sections(cover_letter)
        # 각 항목별로 마크다운 '**' 완전 제거
        growth = re.sub(r'\*\*', '', growth)
        motivation = re.sub(r'\*\*', '', motivation)
        experience = re.sub(r'\*\*', '', experience)
        plan = re.sub(r'\*\*', '', plan)
        html = f"""
        <!DOCTYPE html>
        <html lang=\"ko\">
        <head>
            <meta charset=\"UTF-8\">
            <style>
                @page {{ size: A4; margin: 0; }}
                body {{ font-family: 'Batang', serif; margin: 0; padding: 0; line-height: 1.5; }}
                .page {{ width: 210mm; min-height: 297mm; padding: 15mm 20mm; box-sizing: border-box; }}
                .cover-letter-title {{ font-size: 28px; font-weight: bold; margin-bottom: 40px; text-align: center; letter-spacing: 10px; }}
                .section {{ border: 2px solid #000; margin-bottom: 30px; padding: 18px 20px; border-radius: 6px; page-break-inside: avoid; }}
                .section-title {{ font-weight: bold; font-size: 16px; margin-bottom: 10px; }}
                .section-content {{ white-space: pre-wrap; font-size: 13px; }}
                .footer {{ margin-top: 60px; text-align: center; font-size: 12px; }}
                .date-line {{ margin: 30px 0; line-height: 2; }}
            </style>
        </head>
        <body>
            <div class=\"page\">
                <div class=\"cover-letter-title\">자기소개서</div>
                <div class=\"section section1\">
                    <div class=\"section-title\">1. 성장 과정 및 가치관</div>
                    <div class=\"section-content\">{growth}</div>
                </div>
                <div class=\"section section2\">
                    <div class=\"section-title\">2. 지원 동기 및 포부</div>
                    <div class=\"section-content\">{motivation}</div>
                </div>
                <div class=\"section section3\">
                    <div class=\"section-title\">3. 역량 및 경험</div>
                    <div class=\"section-content\">{experience}</div>
                </div>
                <div class=\"section section4\">
                    <div class=\"section-title\">4. 입사 후 계획</div>
                    <div class=\"section-content\">{plan}</div>
                </div>
                <div class=\"footer\">
                    <p>위의 기재한 내용이 사실과 다름이 없습니다.</p>
                    <div class=\"date-line\">{datetime.now().strftime('%Y년 %m월 %d일')}</div>
                    <p>{user_name} (인)</p>
                </div>
            </div>
        </body>
        </html>
        """
        return html 