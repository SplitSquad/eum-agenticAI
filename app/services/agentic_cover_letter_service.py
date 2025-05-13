    def _generate_cover_letter(self, state: CoverLetterConversationState) -> str:
        """자기소개서 생성"""
        prompt = f"""다음 정보를 바탕으로 자기소개서를 작성해주세요:

지원 직무: {state.job_keywords}
경력 및 경험: {state.experience}
지원 동기: {state.motivation}

다음 형식으로 작성해주세요:
1. 성장 과정 및 가치관
2. 지원 동기 및 포부
3. 역량 및 경험
4. 입사 후 계획

각 섹션은 마크다운 형식으로 작성해주세요.
"""
        response = self.llm_service.generate_text(prompt)
        return response 