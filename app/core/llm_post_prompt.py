class Prompt():
    @staticmethod
    def post_prompt() :
        prompt = f"""
        1. must be return the title and tag. 
        2. must Choose from examples. 
        3. must be select something related to user_input.
        
        default. Please do not create titles and tags arbitrarily.

        <few-shot-example>
        ------------------------
        input : temple, stay, meditation, culture
        output :
            title : 여행
            tags : 
                관광/체험
    
       
        ⚠️ Do NOT include any explanation or message. ONLY return a valid JSON object. No natural language..
        """

        return prompt
    
    @staticmethod
    def post_creation_form():
        prompt = f"""
        1. Please create a post creation json.
        2. Please make it like the example (tags is list)

        @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
        !!! if postType is "자유" then address is "자유"
        language example : {"KO", "EN", "JA", "ZH", "DE", "FR", "ES", "RU"}
        ----------------------------------------------------------------------------------------------------
        input : I want to create a post recommending tourist attractions in Jeju Island. , "category": "여행" , "tags": [관광/체험]
        output :  
            "post":  
                "title": "Jeju Island travel recommendations",  
                "content": "We've compiled a list of must-see attractions in Jeju Island! Enjoy a leisurely trip to Seongsan Ilchulbong, Hyeopjae Beach, and Udo.",  
                "category": "여행",  
                "language": "EN",  
                "tags": ["관광/체험"] ,  
                "postType": "자유",  
                "address": "자유"  
        
        @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@

                
        ⚠️ Do NOT include any explanation or message. ONLY return a valid JSON object. No natural language.

        """

    @staticmethod
    def make_user_data() : 

        prompt= f"""

        1. Please return a dict.
        2. Please return them all as in the example. (If there is no value, return blank.)

        [one-shot]
        input:
            Collected user information : <collected_user_data> 
            Saved user information : <user_info> + <preference_info> 
        output:
            "name": "홍길동",
            "birth": "1990-01-01",
            "phone": "010-1234-5678",
            "nationality": "대한민국",

            "relation1": "부",
            "name1": "홍아버지",
            "age1": "65",
            "job1": "교사",

            "relation2": "모",
            "name2": "홍어머니",
            "age2": "63",
            "job2": "주부",

            "relation3": "형",
            "name3": "홍형",
            "age3": "35",
            "job3": "회사원",

            "address": "서울특별시 강남구 테헤란로 123",
            "email": "hong@example.com",

            "edu_period1": "2009.03 ~ 2013.02",
            "edu_detail1": "서울대학교 컴퓨터공학과 졸업",

            "edu_period2": "2014.06",
            "edu_detail2": "정보처리기사 자격증 취득",

            "career_period1": "2015.03 ~ 2020.12",
            "career_detail1": "네이버 백엔드 개발자",
            "career_note1": "검색 플랫폼 개발",

            "career_period2": "2021.01 ~ 현재",
            "career_detail2": "카카오 시니어 개발자",
            "career_note2": "AI 챗봇 서비스 개발",

            "written_date": "2025년 5월 19일"

        """
        
        return prompt
    

