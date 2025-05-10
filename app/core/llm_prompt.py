class Prompt():
    @staticmethod
    def post_prompt() :
        prompt = f"""
        1. must be return the title and tag.
        2. must be select something related to user_input.
        
        default. Please do not create titles and tags arbitrarily.

        <few-shot-example>
        ------------------------
        input : I want to try making traditional Korean crafts.
        output :
            title : 여행
            tags : 
                관광/체험
        ------------------------
        input : I went to a famous noodle restaurant in Busan.
        output :
            title : 여행
            tags : 
                식도락/맛집
        ------------------------
        input : How do I use the subway in Seoul?
        output :
            title : 여행
            tags : 
                교통/이동
        ------------------------
        input : Can you recommend a good hotel near the beach?
        output :
            title : 여행
            tags : 
                숙소/지역정보
        ------------------------
        input : What should I do if I lose my passport abroad?
        output :
            title : 여행
            tags : 
                대사관/응급
        ------------------------
        input : I joined a kimchi-making class during my trip.
        output :
            title : 여행
            tags : 
                관광/체험
        ------------------------
        input : The street food at the night market was amazing!
        output :
            title : 여행
            tags : 
                식도락/맛집
        ------------------------
        input : Is there a bus from the airport to the city center?
        output :
            title : 여행
            tags : 
                교통/이동
        ------------------------
        input : I found a cozy guesthouse in a traditional village.
        output :
            title : 여행
            tags : 
                숙소/지역정보
        ------------------------
        input : Where is the nearest embassy for emergencies?
        output :
            title : 여행
            tags : 
                대사관/응급
        ------------------------
        input : How do I sign a lease for an apartment in Korea?
        output :
            title : 주거
            tags :
                부동산/계약
        ------------------------
        input : Is there a supermarket near my place?
        output :
            title : 주거
            tags :
                생활환경/편의
        ------------------------
        input : What are some local customs in Korean neighborhoods?
        output :
            title : 주거
            tags :
                문화/생활
        ------------------------
        input : How do I take out the trash properly in my apartment?
        output :
            title : 주거
            tags :
                주거지 관리/유지
        ------------------------
        input : What documents do I need for a rental contract?
        output :
            title : 주거
            tags :
                부동산/계약
        ------------------------
        input : Where can I find a laundromat nearby?
        output :
            title : 주거
            tags :
                생활환경/편의
        ------------------------
        input : People in my area always greet neighbors. Is that common?
        output :
            title : 주거
            tags :
                문화/생활
        ------------------------
        input : My sink is leaking. Who should I call?
        output :
            title : 주거
            tags :
                주거지 관리/유지
        ------------------------
        input : Can foreigners rent apartments without a guarantor?
        output :
            title : 주거
            tags :
                부동산/계약
        ------------------------
        input : Is this neighborhood safe and quiet?
        output :
            title : 주거
            tags :
                생활환경/편의
        ------------------------
        input :I want to write an article about iMac.
        output :
            title : 주거
            tags :
                생활환경/편의
        ------------------------
        input : What's it like living in a dorm in Korea?
        output :
            title : 유학
            tags :
                기숙사/주거
        ------------------------
        input : Tell me about daily life on a Korean university campus.
        output :
            title : 유학
            tags :
                학사/캠퍼스
        ------------------------
        input : Are there academic support centers at Korean universities?
        output :
            title : 유학
            tags :
                학업지원/시설
        ------------------------
        input : What documents do I need to apply for a student visa?
        output :
            title : 유학
            tags :
                행정/비자/서류
        ------------------------
        input : How do I write a Korean-style resume?
        output :
            title : 취업
            tags :
                이력/채용준비
        ------------------------
        input :I want to write an article about iMac.
        output :
            title : 주거
            tags :
                생활환경/편의
        ------------------------
        input : What kind of visa do I need to work in Korea?
        output :
            title : 취업
            tags :
                비자/법률/노동
        ------------------------
        input : Are there any job fairs for international students?
        output :
            title : 취업
            tags :
                잡페어/네트워킹
        ------------------------
        input : I'm looking for a part-time job near my university.
        output :
            title : 취업
            tags :
                알바/파트타임
        ------------------------
        input : How can I prepare for a job interview in Korea?
        output :
            title : 취업
            tags :
                이력/채용준비
        ------------------------
        input : Can I work in Korea with a student visa?
        output :
            title : 취업
            tags :
                비자/법률/노동
        ------------------------
        input : Where can I meet recruiters or companies?
        output :
            title : 취업
            tags :
                잡페어/네트워킹
        ------------------------
        input :I want to write an article about iMac.
        output :
            title : 주거
            tags :
                생활환경/편의
        ------------------------
        input : Any tips for finding weekend part-time work?
        output :
            title : 취업
            tags :
                알바/파트타임
        ------------------------
        input : What documents are required for a job application?
        output :
            title : 취업
            tags :
                이력/채용준비
        ------------------------
        input : What are Korea’s labor laws for foreigners?
        output :
            title : 취업
            tags :
                비자/법률/노동
        ------------------------
        input : I want to try making traditional Korean crafts.
        output :
            title : 여행
            tags : 
                관광/체험
        ------------------------
        input : I went to a famous noodle restaurant in Busan.
        output :
            title : 여행
            tags : 
                식도락/맛집
        ------------------------
        input : How do I use the subway in Seoul?
        output :
            title : 여행
            tags : 
                교통/이동
        ------------------------
        input : Can you recommend a good hotel near the beach?
        output :
            title : 여행
            tags : 
                숙소/지역정보
        ------------------------
        input : What should I do if I lose my passport abroad?
        output :
            title : 여행
            tags : 
                대사관/응급
        ------------------------
        input : I joined a kimchi-making class during my trip.
        output :
            title : 여행
            tags : 
                관광/체험
        ------------------------
        input : The street food at the night market was amazing!
        output :
            title : 여행
            tags : 
                식도락/맛집
        ------------------------
        input : Is there a bus from the airport to the city center?
        output :
            title : 여행
            tags : 
                교통/이동
        ------------------------
        input : I found a cozy guesthouse in a traditional village.
        output :
            title : 여행
            tags : 
                숙소/지역정보
        ------------------------
        input : Where is the nearest embassy for emergencies?
        output :
            title : 여행
            tags : 
                대사관/응급
        ------------------------
        input : How do I sign a lease for an apartment in Korea?
        output :
            title : 주거
            tags :
                부동산/계약
        ------------------------
        input : Is there a supermarket near my place?
        output :
            title : 주거
            tags :
                생활환경/편의
        ------------------------
        input : What are some local customs in Korean neighborhoods?
        output :
            title : 주거
            tags :
                문화/생활
        ------------------------
        input : How do I take out the trash properly in my apartment?
        output :
            title : 주거
            tags :
                주거지 관리/유지
        ------------------------
        input : What documents do I need for a rental contract?
        output :
            title : 주거
            tags :
                부동산/계약
        ------------------------
        input : Where can I find a laundromat nearby?
        output :
            title : 주거
            tags :
                생활환경/편의
        ------------------------
        input : People in my area always greet neighbors. Is that common?
        output :
            title : 주거
            tags :
                문화/생활
        ------------------------
        input : My sink is leaking. Who should I call?
        output :
            title : 주거
            tags :
                주거지 관리/유지
        ------------------------
        input : Can foreigners rent apartments without a guarantor?
        output :
            title : 주거
            tags :
                부동산/계약
        ------------------------
        input : Is this neighborhood safe and quiet?
        output :
            title : 주거
            tags :
                생활환경/편의
        ------------------------
        input : What's it like living in a dorm in Korea?
        output :
            title : 유학
            tags :
                기숙사/주거
        ------------------------
        input : Tell me about daily life on a Korean university campus.
        output :
            title : 유학
            tags :
                학사/캠퍼스
        ------------------------
        input : Are there academic support centers at Korean universities?
        output :
            title : 유학
            tags :
                학업지원/시설
        ------------------------
        input : What documents do I need to apply for a student visa?
        output :
            title : 유학
            tags :
                행정/비자/서류
        ------------------------
        input : How do I write a Korean-style resume?
        output :
            title : 취업
            tags :
                이력/채용준비
        ------------------------
        input : What kind of visa do I need to work in Korea?
        output :
            title : 취업
            tags :
                비자/법률/노동
        ------------------------
        input : Are there any job fairs for international students?
        output :
            title : 취업
            tags :
                잡페어/네트워킹
        ------------------------
        input : I'm looking for a part-time job near my university.
        output :
            title : 취업
            tags :
                알바/파트타임
        ------------------------
        input : How can I prepare for a job interview in Korea?
        output :
            title : 취업
            tags :
                이력/채용준비
        ------------------------
        input : Can I work in Korea with a student visa?
        output :
            title : 취업
            tags :
                비자/법률/노동
        ------------------------
        input : Where can I meet recruiters or companies?
        output :
            title : 취업
            tags :
                잡페어/네트워킹
        ------------------------
        input : Any tips for finding weekend part-time work?
        output :
            title : 취업
            tags :
                알바/파트타임
        ------------------------
        input : What documents are required for a job application?
        output :
            title : 취업
            tags :
                이력/채용준비
        ------------------------
        input : What are Korea’s labor laws for foreigners?
        output :
            title : 취업
            tags :
                비자/법률/노동
        ------------------------
        input : I want to try making traditional Korean crafts.
        output :
            title : 여행
            tags : 
                관광/체험
        ------------------------
        input : I went to a famous noodle restaurant in Busan.
        output :
            title : 여행
            tags : 
                식도락/맛집
        ------------------------
        input : How do I use the subway in Seoul?
        output :
            title : 여행
            tags : 
                교통/이동
        ------------------------
        input : Can you recommend a good hotel near the beach?
        output :
            title : 여행
            tags : 
                숙소/지역정보
        ------------------------
        input : What should I do if I lose my passport abroad?
        output :
            title : 여행
            tags : 
                대사관/응급
        ------------------------
        input : I joined a kimchi-making class during my trip.
        output :
            title : 여행
            tags : 
                관광/체험
        ------------------------
        input : The street food at the night market was amazing!
        output :
            title : 여행
            tags : 
                식도락/맛집
        ------------------------
        input : Is there a bus from the airport to the city center?
        output :
            title : 여행
            tags : 
                교통/이동
        ------------------------
        input : I found a cozy guesthouse in a traditional village.
        output :
            title : 여행
            tags : 
                숙소/지역정보
        ------------------------
        input : Where is the nearest embassy for emergencies?
        output :
            title : 여행
            tags : 
                대사관/응급
        ------------------------
        input : How do I sign a lease for an apartment in Korea?
        output :
            title : 주거
            tags :
                부동산/계약
        ------------------------
        input : Is there a supermarket near my place?
        output :
            title : 주거
            tags :
                생활환경/편의
        ------------------------
        input : What are some local customs in Korean neighborhoods?
        output :
            title : 주거
            tags :
                문화/생활
        ------------------------
        input : How do I take out the trash properly in my apartment?
        output :
            title : 주거
            tags :
                주거지 관리/유지
        ------------------------
        input : What documents do I need for a rental contract?
        output :
            title : 주거
            tags :
                부동산/계약
        ------------------------
        input : Where can I find a laundromat nearby?
        output :
            title : 주거
            tags :
                생활환경/편의
        ------------------------
        input : People in my area always greet neighbors. Is that common?
        output :
            title : 주거
            tags :
                문화/생활
        ------------------------
        input : My sink is leaking. Who should I call?
        output :
            title : 주거
            tags :
                주거지 관리/유지
        ------------------------
        input : Can foreigners rent apartments without a guarantor?
        output :
            title : 주거
            tags :
                부동산/계약
        ------------------------
        input : Is this neighborhood safe and quiet?
        output :
            title : 주거
            tags :
                생활환경/편의
        ------------------------
        input : What's it like living in a dorm in Korea?
        output :
            title : 유학
            tags :
                기숙사/주거
        ------------------------
        input : Tell me about daily life on a Korean university campus.
        output :
            title : 유학
            tags :
                학사/캠퍼스
        ------------------------
        input : Are there academic support centers at Korean universities?
        output :
            title : 유학
            tags :
                학업지원/시설
        ------------------------
        input : What documents do I need to apply for a student visa?
        output :
            title : 유학
            tags :
                행정/비자/서류
        ------------------------
        input : How do I write a Korean-style resume?
        output :
            title : 취업
            tags :
                이력/채용준비
        ------------------------
        input : What kind of visa do I need to work in Korea?
        output :
            title : 취업
            tags :
                비자/법률/노동
        ------------------------
        input : Are there any job fairs for international students?
        output :
            title : 취업
            tags :
                잡페어/네트워킹
        ------------------------
        input : I'm looking for a part-time job near my university.
        output :
            title : 취업
            tags :
                알바/파트타임
        ------------------------
        input : How can I prepare for a job interview in Korea?
        output :
            title : 취업
            tags :
                이력/채용준비
        ------------------------
        input : Can I work in Korea with a student visa?
        output :
            title : 취업
            tags :
                비자/법률/노동
        ------------------------
        input : Where can I meet recruiters or companies?
        output :
            title : 취업
            tags :
                잡페어/네트워킹
        ------------------------
        input : Any tips for finding weekend part-time work?
        output :
            title : 취업
            tags :
                알바/파트타임
        ------------------------
        input : What documents are required for a job application?
        output :
            title : 취업
            tags :
                이력/채용준비
        ------------------------
        input : What are Korea’s labor laws for foreigners?
        output :
            title : 취업
            tags :
                비자/법률/노동
        ------------------------
        input : I want to try making traditional Korean crafts.
        output :
            title : 여행
            tags : 
                관광/체험
        ------------------------
        input : I went to a famous noodle restaurant in Busan.
        output :
            title : 여행
            tags : 
                식도락/맛집
        ------------------------
        input : How do I use the subway in Seoul?
        output :
            title : 여행
            tags : 
                교통/이동
        ------------------------
        input : Can you recommend a good hotel near the beach?
        output :
            title : 여행
            tags : 
                숙소/지역정보
        ------------------------
        input : What should I do if I lose my passport abroad?
        output :
            title : 여행
            tags : 
                대사관/응급
        ------------------------
        input : I joined a kimchi-making class during my trip.
        output :
            title : 여행
            tags : 
                관광/체험
        ------------------------
        input : The street food at the night market was amazing!
        output :
            title : 여행
            tags : 
                식도락/맛집
        ------------------------
        input : Is there a bus from the airport to the city center?
        output :
            title : 여행
            tags : 
                교통/이동
        ------------------------
        input : I found a cozy guesthouse in a traditional village.
        output :
            title : 여행
            tags : 
                숙소/지역정보
        ------------------------
        input : Where is the nearest embassy for emergencies?
        output :
            title : 여행
            tags : 
                대사관/응급
        ------------------------
        input : How do I sign a lease for an apartment in Korea?
        output :
            title : 주거
            tags :
                부동산/계약
        ------------------------
        input : Is there a supermarket near my place?
        output :
            title : 주거
            tags :
                생활환경/편의
        ------------------------
        input : What are some local customs in Korean neighborhoods?
        output :
            title : 주거
            tags :
                문화/생활
        ------------------------
        input : How do I take out the trash properly in my apartment?
        output :
            title : 주거
            tags :
                주거지 관리/유지
        ------------------------
        input : What documents do I need for a rental contract?
        output :
            title : 주거
            tags :
                부동산/계약
        ------------------------
        input : Where can I find a laundromat nearby?
        output :
            title : 주거
            tags :
                생활환경/편의
        ------------------------
        input : People in my area always greet neighbors. Is that common?
        output :
            title : 주거
            tags :
                문화/생활
        ------------------------
        input : My sink is leaking. Who should I call?
        output :
            title : 주거
            tags :
                주거지 관리/유지
        ------------------------
        input : Can foreigners rent apartments without a guarantor?
        output :
            title : 주거
            tags :
                부동산/계약
        ------------------------
        input : Is this neighborhood safe and quiet?
        output :
            title : 주거
            tags :
                생활환경/편의
        ------------------------
        input : What's it like living in a dorm in Korea?
        output :
            title : 유학
            tags :
                기숙사/주거
        ------------------------
        input : Tell me about daily life on a Korean university campus.
        output :
            title : 유학
            tags :
                학사/캠퍼스
        ------------------------
        input : Are there academic support centers at Korean universities?
        output :
            title : 유학
            tags :
                학업지원/시설
        ------------------------
        input : What documents do I need to apply for a student visa?
        output :
            title : 유학
            tags :
                행정/비자/서류
        ------------------------
        input : How do I write a Korean-style resume?
        output :
            title : 취업
            tags :
                이력/채용준비
        ------------------------
        input : What kind of visa do I need to work in Korea?
        output :
            title : 취업
            tags :
                비자/법률/노동
        ------------------------
        input : Are there any job fairs for international students?
        output :
            title : 취업
            tags :
                잡페어/네트워킹
        ------------------------
        input : I'm looking for a part-time job near my university.
        output :
            title : 취업
            tags :
                알바/파트타임
        ------------------------
        input : How can I prepare for a job interview in Korea?
        output :
            title : 취업
            tags :
                이력/채용준비
        ------------------------
        input : Can I work in Korea with a student visa?
        output :
            title : 취업
            tags :
                비자/법률/노동
        ------------------------
        input : Where can I meet recruiters or companies?
        output :
            title : 취업
            tags :
                잡페어/네트워킹
        ------------------------
        input : Any tips for finding weekend part-time work?
        output :
            title : 취업
            tags :
                알바/파트타임
        ------------------------
        input : What documents are required for a job application?
        output :
            title : 취업
            tags :
                이력/채용준비
        ------------------------
        input : What are Korea’s labor laws for foreigners?
        output :
            title : 취업
            tags :
                비자/법률/노동
        ------------------------
        input : I want to try making traditional Korean crafts.
        output :
            title : 여행
            tags : 
                관광/체험
        ------------------------
        input : I went to a famous noodle restaurant in Busan.
        output :
            title : 여행
            tags : 
                식도락/맛집
        ------------------------
        input : How do I use the subway in Seoul?
        output :
            title : 여행
            tags : 
                교통/이동
        ------------------------
        input : Can you recommend a good hotel near the beach?
        output :
            title : 여행
            tags : 
                숙소/지역정보
        ------------------------
        input : What should I do if I lose my passport abroad?
        output :
            title : 여행
            tags : 
                대사관/응급
        ------------------------
        input : I joined a kimchi-making class during my trip.
        output :
            title : 여행
            tags : 
                관광/체험
        ------------------------
        input : The street food at the night market was amazing!
        output :
            title : 여행
            tags : 
                식도락/맛집
        ------------------------
        input : Is there a bus from the airport to the city center?
        output :
            title : 여행
            tags : 
                교통/이동
        ------------------------
        input : I found a cozy guesthouse in a traditional village.
        output :
            title : 여행
            tags : 
                숙소/지역정보
        ------------------------
        input : Where is the nearest embassy for emergencies?
        output :
            title : 여행
            tags : 
                대사관/응급
        ------------------------
        input : How do I sign a lease for an apartment in Korea?
        output :
            title : 주거
            tags :
                부동산/계약
        ------------------------
        input : Is there a supermarket near my place?
        output :
            title : 주거
            tags :
                생활환경/편의
        ------------------------
        input : What are some local customs in Korean neighborhoods?
        output :
            title : 주거
            tags :
                문화/생활
        ------------------------
        input : How do I take out the trash properly in my apartment?
        output :
            title : 주거
            tags :
                주거지 관리/유지
        ------------------------
        input : What documents do I need for a rental contract?
        output :
            title : 주거
            tags :
                부동산/계약
        ------------------------
        input : Where can I find a laundromat nearby?
        output :
            title : 주거
            tags :
                생활환경/편의
        ------------------------
        input : People in my area always greet neighbors. Is that common?
        output :
            title : 주거
            tags :
                문화/생활
        ------------------------
        input : My sink is leaking. Who should I call?
        output :
            title : 주거
            tags :
                주거지 관리/유지
        ------------------------
        input : Can foreigners rent apartments without a guarantor?
        output :
            title : 주거
            tags :
                부동산/계약
        ------------------------
        input : Is this neighborhood safe and quiet?
        output :
            title : 주거
            tags :
                생활환경/편의
        ------------------------
        input : What's it like living in a dorm in Korea?
        output :
            title : 유학
            tags :
                기숙사/주거
        ------------------------
        input : Tell me about daily life on a Korean university campus.
        output :
            title : 유학
            tags :
                학사/캠퍼스
        ------------------------
        input : Are there academic support centers at Korean universities?
        output :
            title : 유학
            tags :
                학업지원/시설
        ------------------------
        input : What documents do I need to apply for a student visa?
        output :
            title : 유학
            tags :
                행정/비자/서류
        ------------------------
        input : How do I write a Korean-style resume?
        output :
            title : 취업
            tags :
                이력/채용준비
        ------------------------
        input : What kind of visa do I need to work in Korea?
        output :
            title : 취업
            tags :
                비자/법률/노동
        ------------------------
        input : Are there any job fairs for international students?
        output :
            title : 취업
            tags :
                잡페어/네트워킹
        ------------------------
        input : I'm looking for a part-time job near my university.
        output :
            title : 취업
            tags :
                알바/파트타임
        ------------------------
        input : How can I prepare for a job interview in Korea?
        output :
            title : 취업
            tags :
                이력/채용준비
        ------------------------
        input : Can I work in Korea with a student visa?
        output :
            title : 취업
            tags :
                비자/법률/노동
        ------------------------
        input : Where can I meet recruiters or companies?
        output :
            title : 취업
            tags :
                잡페어/네트워킹
        ------------------------
        input : Any tips for finding weekend part-time work?
        output :
            title : 취업
            tags :
                알바/파트타임
        ------------------------
        input : What documents are required for a job application?
        output :
            title : 취업
            tags :
                이력/채용준비
        ------------------------
        input : What are Korea’s labor laws for foreigners?
        output :
            title : 취업
            tags :
                비자/법률/노동
        ------------------------

        ⚠️ Do NOT include any explanation or message. ONLY return a valid JSON object. No natural language..
        """

        return prompt