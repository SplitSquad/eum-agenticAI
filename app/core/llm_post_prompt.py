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
        ------------------------
        input : traditional, market, tour, local food
        output :
            title : 여행
            tags : 
                관광/체험
        ------------------------
        input : hanbok, rental, photo, experience
        output :
            title : 여행
            tags : 
                관광/체험
        ------------------------
        input : ceramic, workshop, pottery, making
        output :
            title : 여행
            tags : 
                관광/체험
        ------------------------
        input : palace, tour, guide, history
        output :
            title : 여행
            tags : 
                관광/체험
        ------------------------
        input : famous, noodle, restaurant, Busan
        output :
            title : 여행
            tags : 
                식도락/맛집
        ------------------------
        input : street, food, Seoul, night market
        output :
            title : 여행
            tags : 
                식도락/맛집
        ------------------------
        input : traditional, Korean, barbecue, experience
        output :
            title : 여행
            tags : 
                식도락/맛집
        ------------------------
        input : seafood, market, fresh, tasting
        output :
            title : 여행
            tags : 
                식도락/맛집
        ------------------------
        input : cafe, dessert, review, Jeju
        output :
            title : 여행
            tags : 
                식도락/맛집
        ------------------------
        input : subway, Seoul, how to use
        output :
            title : 여행
            tags : 
                교통/이동
        ------------------------
        input : taxi, Tokyo, cost
        output :
            title : 여행
            tags : 
                교통/이동
        ------------------------
        input : airport, transportation, best way
        output :
            title : 여행
            tags : 
                교통/이동
        ------------------------
        input : car rental, Jeju
        output :
            title : 여행
            tags : 
                교통/이동
        ------------------------
        input : train pass, Japan, tourist
        output :
            title : 여행
            tags : 
                교통/이동
        ------------------------
        input : hotel, beach, recommendation
        output :
            title : 여행
            tags : 
                숙소/지역정보
        ------------------------
        input : hostel, Europe, safety
        output :
            title : 여행
            tags : 
                숙소/지역정보
        ------------------------
        input : Paris, best area, stay
        output :
            title : 여행
            tags : 
                숙소/지역정보
        ------------------------
        input : cheap accommodation, New York
        output :
            title : 여행
            tags : 
                숙소/지역정보
        ------------------------
        input : guesthouse, Busan, location
        output :
            title : 여행
            tags : 
                숙소/지역정보
        ------------------------
        input : lost passport, abroad, what to do
        output :
            title : 여행
            tags : 
                대사관/응급
        ------------------------
        input : embassy, contact, overseas
        output :
            title : 여행
            tags : 
                대사관/응급
        ------------------------
        input : emergency, hospital, travel
        output :
            title : 여행
            tags : 
                대사관/응급
        ------------------------
        input : travel insurance, medical, coverage
        output :
            title : 여행
            tags : 
                대사관/응급
        ------------------------
        input : embassy, Bangkok, nearest
        output :
            title : 여행
            tags : 
                대사관/응급
        ------------------------
        input : lease, apartment, Korea, how to sign
        output :
            title : 주거
            tags :
                부동산/계약
        ------------------------
        input : housing contract, documents, requirements
        output :
            title : 주거
            tags :
                부동산/계약
        ------------------------
        input : monthly rent, key money, difference
        output :
            title : 주거
            tags :
                부동산/계약
        ------------------------
        input : real estate agent, find apartment
        output :
            title : 주거
            tags :
                부동산/계약
        ------------------------
        input : deposit, apartment, Korea
        output :
            title : 주거
            tags :
                부동산/계약
        ------------------------
        input : supermarket, nearby, location
        output :
            title : 주거
            tags :
                생활환경/편의
        ------------------------
        input : laundromat, walking distance
        output :
            title : 주거
            tags :
                생활환경/편의
        ------------------------
        input : bus stop, close to home
        output :
            title : 주거
            tags :
                생활환경/편의
        ------------------------
        input : convenience store, nearest
        output :
            title : 주거
            tags :
                생활환경/편의
        ------------------------
        input : pharmacy, open late, neighborhood
        output :
            title : 주거
            tags :
                생활환경/편의
        ------------------------
        input : Korean neighbors, customs
        output :
            title : 주거
            tags :
                문화/생활
        ------------------------
        input : etiquette, living in Korean apartment
        output :
            title : 주거
            tags :
                문화/생활
        ------------------------
        input : noise rules, Korea, apartment
        output :
            title : 주거
            tags :
                문화/생활
        ------------------------
        input : quiet hours, residential area, Korea
        output :
            title : 주거
            tags :
                문화/생활
        ------------------------
        input : greeting neighbors, Korean culture
        output :
            title : 주거
            tags :
                문화/생활
        ------------------------
        input : trash, apartment, how to separate
        output :
            title : 주거
            tags :
                주거지 관리/유지
        ------------------------
        input : recycling rules, Korea, apartment
        output :
            title : 주거
            tags :
                주거지 관리/유지
        ------------------------
        input : broken light, apartment, repair
        output :
            title : 주거
            tags :
                주거지 관리/유지
        ------------------------
        input : cleaning schedule, shared space
        output :
            title : 주거
            tags :
                주거지 관리/유지
        ------------------------
        input : water leak, who to call
        output :
            title : 주거
            tags :
                주거지 관리/유지
        ------------------------
        input : dormitory, life, Korea, student
        output :
            title : 유학
            tags :
                기숙사/주거
        ------------------------
        input : student housing, dormitory rules, Korean university
        output :
            title : 유학
            tags :
                기숙사/주거
        ------------------------
        input : living in campus dorm, Korea
        output :
            title : 유학
            tags :
                기숙사/주거
        ------------------------
        input : roommate, dormitory, lifestyle, Korea
        output :
            title : 유학
            tags :
                기숙사/주거
        ------------------------
        input : dorm fees, Korean universities
        output :
            title : 유학
            tags :
                기숙사/주거
        ------------------------
        input : daily life, Korean campus, student
        output :
            title : 유학
            tags :
                학사/캠퍼스
        ------------------------
        input : university clubs, activities, Korea
        output :
            title : 유학
            tags :
                학사/캠퍼스
        ------------------------
        input : Korean university schedule, life
        output :
            title : 유학
            tags :
                학사/캠퍼스
        ------------------------
        input : student cafeteria, campus facilities
        output :
            title : 유학
            tags :
                학사/캠퍼스
        ------------------------
        input : how to register for classes, Korean campus
        output :
            title : 유학
            tags :
                학사/캠퍼스
        ------------------------
        input : academic help center, Korean university
        output :
            title : 유학
            tags :
                학업지원/시설
        ------------------------
        input : writing center, study support, university
        output :
            title : 유학
            tags :
                학업지원/시설
        ------------------------
        input : tutoring, academic support, Korea
        output :
            title : 유학
            tags :
                학업지원/시설
        ------------------------
        input : Korean university, library services
        output :
            title : 유학
            tags :
                학업지원/시설
        ------------------------
        input : study resources, campus support
        output :
            title : 유학
            tags :
                학업지원/시설
        ------------------------
        input : student visa, required documents, Korea
        output :
            title : 유학
            tags :
                행정/비자/서류
        ------------------------
        input : visa application, process, study abroad
        output :
            title : 유학
            tags :
                행정/비자/서류
        ------------------------
        input : visa issuance, embassy, student
        output :
            title : 유학
            tags :
                행정/비자/서류
        ------------------------
        input : visa interview, documents, studying in Korea
        output :
            title : 유학
            tags :
                행정/비자/서류
        ------------------------
        input : D-2 visa, requirements
        output :
            title : 유학
            tags :
                행정/비자/서류
        ------------------------
        input : Korean, resume, write, style
        output :
            title : 취업
            tags :
                이력/채용준비
        ------------------------
        input : job resume, Korea, format, tips
        output :
            title : 취업
            tags :
                이력/채용준비
        ------------------------
        input : Korean-style CV, example, application
        output :
            title : 취업
            tags :
                이력/채용준비
        ------------------------
        input : resume, layout, Korean job market
        output :
            title : 취업
            tags :
                이력/채용준비
        ------------------------
        input : cover letter, Korean job application
        output :
            title : 취업
            tags :
                이력/채용준비
        ------------------------
        input : work, visa, Korea, requirement
        output :
            title : 취업
            tags :
                비자/법률/노동
        ------------------------
        input : employment visa, process, Korea
        output :
            title : 취업
            tags :
                비자/법률/노동
        ------------------------
        input : labor law, foreign workers, Korea
        output :
            title : 취업
            tags :
                비자/법률/노동
        ------------------------
        input : legal issues, work permit, Korea
        output :
            title : 취업
            tags :
                비자/법률/노동
        ------------------------
        input : visa types, working in Korea
        output :
            title : 취업
            tags :
                비자/법률/노동
        ------------------------
        input : job fair, international students, Korea
        output :
            title : 취업
            tags :
                잡페어/네트워킹
        ------------------------
        input : networking, career expo, Korea
        output :
            title : 취업
            tags :
                잡페어/네트워킹
        ------------------------
        input : foreigner, job fair, Korean university
        output :
            title : 취업
            tags :
                잡페어/네트워킹
        ------------------------
        input : employment event, student, networking
        output :
            title : 취업
            tags :
                잡페어/네트워킹
        ------------------------
        input : university, career event, job
        output :
            title : 취업
            tags :
                잡페어/네트워킹
        ------------------------
        input : part-time, university, job, nearby
        output :
            title : 취업
            tags :
                알바/파트타임
        ------------------------
        input : student job, part-time, location, Korea
        output :
            title : 취업
            tags :
                알바/파트타임
        ------------------------
        input : part-time, cafe, job, weekend
        output :
            title : 취업
            tags :
                알바/파트타임
        ------------------------
        input : hourly job, student, work
        output :
            title : 취업
            tags :
                알바/파트타임
        ------------------------
        input : part-time work, convenience store, apply
        output :
            title : 취업
            tags :
                알바/파트타임
        ------------------------
        input : lost item, airport, report
        output :
            title : 여행
            tags :
                대사관/응급
        ------------------------
        input : hiking, trail, national park
        output :
            title : 여행
            tags :
                관광/체험
        ------------------------
        input : language barrier, travel, translation app
        output :
            title : 여행
            tags :
                대사관/응급
        ------------------------
        input : traditional tea ceremony, Korea
        output :
            title : 여행
            tags :
                관광/체험
        ------------------------
        input : seafood, allergy, travel, safety
        output :
            title : 여행
            tags :
                대사관/응급
        ------------------------
        input : finding vegan food, abroad
        output :
            title : 여행
            tags :
                식도락/맛집
        ------------------------
        input : student health insurance, Korea
        output :
            title : 유학
            tags :
                행정/비자/서류
        ------------------------
        input : university, orientation, guidebook
        output :
            title : 유학
            tags :
                학사/캠퍼스
        ------------------------
        input : volunteer work, campus, experience
        output :
            title : 유학
            tags :
                학사/캠퍼스
        ------------------------
        input : mail service, student dorm
        output :
            title : 유학
            tags :
                기숙사/주거
        ------------------------
        input : dormitory internet issue, who to ask
        output :
            title : 유학
            tags :
                기숙사/주거
        ------------------------
        input : visa extension, procedures
        output :
            title : 유학
            tags :
                행정/비자/서류
        ------------------------
        input : local job board, find work
        output :
            title : 취업
            tags :
                알바/파트타임
        ------------------------
        input : career counseling, Korean university
        output :
            title : 취업
            tags :
                이력/채용준비
        ------------------------
        input : remote work, legal status, Korea
        output :
            title : 취업
            tags :
                비자/법률/노동
        ------------------------
        input : applying for E-7 visa, Korea
        output :
            title : 취업
            tags :
                비자/법률/노동
        ------------------------
        input : preparing for job interview, Korea
        output :
            title : 취업
            tags :
                이력/채용준비
        ------------------------
        input : seasonal job, tourist area
        output :
            title : 취업
            tags :
                알바/파트타임
        ------------------------
        input : renting office space, Korea
        output :
            title : 주거
            tags :
                부동산/계약
        ------------------------
        input : housewarming, Korean custom
        output :
            title : 주거
            tags :
                문화/생활
        ------------------------
        input : neighborhood safety, checking tips
        output :
            title : 주거
            tags :
                생활환경/편의
        ------------------------
        input : utility bills, how to pay
        output :
            title : 주거
            tags :
                주거지 관리/유지
        ------------------------
        input : electricity outage, apartment
        output :
            title : 주거
            tags :
                주거지 관리/유지
        ------------------------
        input : Airbnb rules, Korea
        output :
            title : 여행
            tags :
                숙소/지역정보
        ------------------------
        input : bicycle rental, city tour
        output :
            title : 여행
            tags :
                교통/이동
        ------------------------
        input : taking pet abroad, flight tips
        output :
            title : 여행
            tags :
                대사관/응급
        ------------------------
        input : local sim card, internet access
        output :
            title : 여행
            tags :
                생활환경/편의
        ------------------------
        input : apply for ARC, foreigner in Korea
        output :
            title : 유학
            tags :
                행정/비자/서류
        ------------------------
        input : Korean resume, photo requirements
        output :
            title : 취업
            tags :
                이력/채용준비
        ------------------------
        input : tax filing, part-time job, student
        output :
            title : 취업
            tags :
                비자/법률/노동
        ------------------------
        input : mobile payment, Korea, setup
        output :
            title : 주거
            tags :
                생활환경/편의
        ------------------------
        input : fire drill, apartment building
        output :
            title : 주거
            tags :
                주거지 관리/유지
        ------------------------
        input : public library, Korea, how to use
        output :
            title : 유학
            tags :
                학업지원/시설
        ------------------------
        input : how to use coin laundry, dormitory
        output :
            title : 유학
            tags :
                기숙사/주거
        ------------------------
        input : course withdrawal, Korean university
        output :
            title : 유학
            tags :
                학사/캠퍼스
        ------------------------
        input : cultural festival, university event
        output :
            title : 유학
            tags :
                학사/캠퍼스
        ------------------------
        input : how to apply for scholarship, Korea
        output :
            title : 유학
            tags :
                학업지원/시설
        ------------------------
        input : changing major, Korean university
        output :
            title : 유학
            tags :
                학사/캠퍼스
        ------------------------
        input : school holidays, Korea, calendar
        output :
            title : 유학
            tags :
                학사/캠퍼스
        ------------------------
        input : coffee shop, review, Hongdae
        output :
            title : 여행
            tags :
                식도락/맛집
        ------------------------
        input : festival, fireworks, Han River
        output :
            title : 여행
            tags :
                관광/체험
        ------------------------
        input : beach, surfing, equipment rental
        output :
            title : 여행
            tags :
                관광/체험
        ------------------------
        input : glamping, weekend trip, near Seoul
        output :
            title : 여행
            tags :
                관광/체험
        ------------------------
        input : late-night food, delivery, Korea
        output :
            title : 여행
            tags :
                식도락/맛집
        ------------------------
        input : train, KTX, schedule, booking
        output :
            title : 여행
            tags :
                교통/이동
        ------------------------
        input : how to get to airport from city
        output :
            title : 여행
            tags :
                교통/이동
        ------------------------
        input : express bus, intercity travel
        output :
            title : 여행
            tags :
                교통/이동
        ------------------------
        input : youth hostel, Seoul, reservation
        output :
            title : 여행
            tags :
                숙소/지역정보
        ------------------------
        input : budget hotel, tips, student
        output :
            title : 여행
            tags :
                숙소/지역정보
        ------------------------
        input : lost phone, what to do, Korea
        output :
            title : 여행
            tags :
                대사관/응급
        ------------------------
        input : emergency number, Korea
        output :
            title : 여행
            tags :
                대사관/응급
        ------------------------
        input : embassy services, passport renewal
        output :
            title : 여행
            tags :
                대사관/응급
        ------------------------
        input : garbage bag, purchase, Korea
        output :
            title : 주거
            tags :
                주거지 관리/유지
        ------------------------
        input : interior decoration, student housing
        output :
            title : 주거
            tags :
                문화/생활
        ------------------------
        input : package delivery, apartment system
        output :
            title : 주거
            tags :
                생활환경/편의
        ------------------------
        input : roommate conflict, dorm rules
        output :
            title : 유학
            tags :
                기숙사/주거
        ------------------------
        input : bank account, open, student
        output :
            title : 유학
            tags :
                행정/비자/서류
        ------------------------
        input : preparing for job interview, student
        output :
            title : 취업
            tags :
                이력/채용준비
        ------------------------
        input : working holiday visa, Korea
        output :
            title : 취업
            tags :
                비자/법률/노동
        ------------------------
        input : job networking event, alumni
        output :
            title : 취업
            tags :
                잡페어/네트워킹
        ------------------------
        input : apartment, view, window, sunlight
        title : 주거
        tags :
            문화/생활
        ------------------------
        input : mobile plan, compare, Korea
        title : 주거
        tags :
            생활환경/편의
        ------------------------
        input : lost luggage, international flight
        title : 여행
        tags :
            대사관/응급
        ------------------------
        input : weekend getaway, nature, Seoul
        title : 여행
        tags :
            관광/체험
        ------------------------
        input : Korean barbecue, how to eat
        title : 여행
        tags :
            식도락/맛집
        ------------------------
        input : subway etiquette, Korea
        title : 여행
        tags :
            교통/이동
        ------------------------
        input : hotel check-in process, tips
        title : 여행
        tags :
            숙소/지역정보
        ------------------------
        input : embassy location, visa help
        title : 여행
        tags :
            대사관/응급
        ------------------------
        input : lease renewal, Korean apartment
        title : 주거
        tags :
            부동산/계약
        ------------------------
        input : buying groceries, Korean mart
        title : 주거
        tags :
            생활환경/편의
        ------------------------
        input : adjusting to new neighborhood
        title : 주거
        tags :
            문화/생활
        ------------------------
        input : fixing plumbing, apartment issue
        title : 주거
        tags :
            주거지 관리/유지
        ------------------------
        input : student dorm, weekend policy
        title : 유학
        tags :
            기숙사/주거
        ------------------------
        input : student ID, campus use
        title : 유학
        tags :
            학사/캠퍼스
        ------------------------
        input : tutoring center, academic help
        title : 유학
        tags :
            학업지원/시설
        ------------------------
        input : visa expiration, reminder
        title : 유학
        tags :
            행정/비자/서류
        ------------------------
        input : resume template, Korean style
        title : 취업
        tags :
            이력/채용준비
        ------------------------
        input : workplace laws, Korea
        title : 취업
        tags :
            비자/법률/노동
        ------------------------
        input : alumni, career network
        title : 취업
        tags :
            잡페어/네트워킹
        ------------------------
        input : bakery job, part-time
        title : 취업
        tags :
            알바/파트타임
        ------------------------
        input : finding housing, near station
        title : 주거
        tags :
            부동산/계약
        ------------------------
        input : hair salon, reservation, Korea
        title : 주거
        tags :
            생활환경/편의
        ------------------------
        input : socializing, Korean neighbors
        title : 주거
        tags :
            문화/생활
        ------------------------
        input : cleaning tools, apartment
        title : 주거
        tags :
            주거지 관리/유지
        ------------------------
        input : dorm check-in process
        title : 유학
        tags :
            기숙사/주거
        ------------------------
        input : course registration system
        title : 유학
        tags :
            학사/캠퍼스
        ------------------------
        input : access to university library
        title : 유학
        tags :
            학업지원/시설
        ------------------------
        input : visa reapplication, documents
        title : 유학
        tags :
            행정/비자/서류
        ------------------------
        input : writing a Korean cover letter
        title : 취업
        tags :
            이력/채용준비
        ------------------------
        input : employer contract, rights
        title : 취업
        tags :
            비자/법률/노동
        ------------------------
        input : university career fair, booth info
        title : 취업
        tags :
            잡페어/네트워킹
        ------------------------
        input : part-time restaurant job, shift
        title : 취업
        tags :
            알바/파트타임
        ------------------------
        input : guesthouse experience, Seoul
        title : 여행
        tags :
            숙소/지역정보
        ------------------------
        input : bus card recharge, station
        title : 여행
        tags :
            교통/이동
        ------------------------
        input : midnight snack, best place
        title : 여행
        tags :
            식도락/맛집
        ------------------------
        input : cherry blossom, picnic spots
        title : 여행
        tags :
            관광/체험
        ------------------------
        input : emergency contact, embassy help
        title : 여행
        tags :
            대사관/응급
        ------------------------
        input : Korean address, how to read
        title : 주거
        tags :
            생활환경/편의
        ------------------------
        input : indoor slippers, Korean habit
        title : 주거
        tags :
            문화/생활
        ------------------------
        input : faulty heater, winter fix
        title : 주거
        tags :
            주거지 관리/유지



       
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
        ----------------------------------------------------------------------------------------------------
        input : 일본 맛집 탐방 후기 작성할래 , "category": "여행" , "tags": [식도락/맛집] 
        output :  
            "post":  
                "title": "오사카 맛집 리스트",  
                "content": "돈카츠, 타코야끼, 오코노미야끼 등 오사카에서 먹어야 할 음식과 위치를 정리해봤어요. 여행 전 참고해보세요!",  
                "category": "여행",  
                "language": "KO",  
                "tags": "[식도락/맛집]",  
                "postType": "자유",  
                "address": "자유"  
        ----------------------------------------------------------------------------------------------------
        input : パリ博物館ツアー会議をしたい , "category": "여행" , "tags": [관광/체험]  
        output :  
            "post":  
                "title": "パリ文化を訪れる",  
                "content": "ルーヴル、オルセ、ロダン美術館ツアー一緒にいただく方募集します。フランス芸術に興味のある方歓迎します！",  
                "category": "여행",  
                "language": "JA",  
                "tags": ["관광/체험"],  
                "postType": "모임",  
                "address": "프랑스 파리"  
        ----------------------------------------------------------------------------------------------------
        input : 我想写一篇总结首尔交通的文章。 ,"category": "여행" , "tags": [교통/이동 ] 
        output :  
            "post":  
                "title": " 首尔交通提示",  
                "content": "我们分享如何在首尔轻松乘坐地铁和公交车、换乘技巧以及如何使用T-money的技巧。",  
                "category": "여행",  
                "language": "ZH",  
                "tags": ["교통/이동"],  
                "postType": "자유",  
                "address": "자유"  
        ----------------------------------------------------------------------------------------------------
        input : Ich werde einen Artikel über Apothekeninformationen für Ausländer schreiben. , "category": "여행" , tags": [대사관/응급]  
        output :  
            "post":  
                "title": "Tipps zur Apothekennutzung für Ausländer",  
                "content": "Wir haben Informationen zu für Ausländer leicht zugänglichen Apotheken und grundlegenden rezeptfreien Medikamenten zusammengestellt.",  
                "category": "여행",  
                "language": "DE",  
                "tags": ["대사관/응급"] ,  
                "postType": "자유",  
                "address": "자유"  
        ----------------------------------------------------------------------------------------------------
        input : Je veux partager des conseils pour utiliser le métro à Séoul. , "category": "여행" , "tags": [교통/이동]
        output :  
            "post":  
                "title": "Se déplacer à Séoul en métro",  
                "content": "Découvrez comment utiliser facilement le métro de Séoul, acheter une carte T-money, et naviguer entre les lignes principales.",  
                "category": "여행",  
                "language": "FR",  
                "tags": ["교통/이동"],  
                "postType": "자유",  
                "address": "Corée du Sud, Séoul"  
        ----------------------------------------------------------------------------------------------------
        input : Quiero escribir una publicación sobre mi experiencia gastronómica en México. , "category": "여행" , "tags": [식도락/맛집]
        output :  
            "post":  
                "title": "Comida callejera que debes probar en México",  
                "content": "Desde tacos y elotes hasta tamales y aguas frescas, comparto mis experiencias y lugares favoritos en la Ciudad de México.",  
                "category": "여행",  
                "language": "ES",  
                "tags": ["식도락/맛집"],  
                "postType": "자유",  
                "address": "Ciudad de México, México"  
        ----------------------------------------------------------------------------------------------------
        input : Хочу поделиться местами, которые стоит посетить в Санкт-Петербурге. , "category": "여행" , "tags": [관광/체험]
        output :  
            "post":  
                "title": "Лучшие туристические места Санкт-Петербурга",  
                "content": "Эрмитаж, Исаакиевский собор и прогулки по Неве — вот что обязательно стоит включить в свой маршрут!",  
                "category": "여행",  
                "language": "RU",  
                "tags": ["관광/체험"],  
                "postType": "자유",  
                "address": "Россия, Санкт-Петербург"  
        ----------------------------------------------------------------------------------------------------

        @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@

                
        ⚠️ Do NOT include any explanation or message. ONLY return a valid JSON object. No natural language.

        """

        return prompt
    

    @staticmethod
    def agentic_classifier_prompt():

        prompt = """
        1. Its role is to inform the category.
        2. Here is a few-shot example.
        -----------------------
        input : Add an event to my calendar  
        output : calendar  
        -----------------------
        input : I have a plan tomorrow  
        output : calendar  
        -----------------------
        input : Schedule a meeting at 3 PM  
        output : calendar  
        -----------------------
        input : Can you register a schedule for me?  
        output : calendar  
        -----------------------
        input : I want to change my appointment  
        output : calendar  
        -----------------------
        input : I have a lunch appointment tomorrow  
        output : calendar  
        -----------------------
        input : There’s a team dinner this Friday  
        output : calendar  
        -----------------------
        input : Check my schedule  
        output : calendar  
        -----------------------
        input : I’d like to add a new event  
        output : calendar  
        -----------------------
        input : Set up a reminder for next Monday  
        output : calendar  
        -----------------------
        input : Add an event to my calendar  
        output : calendar  
        -----------------------
        input : I have a plan tomorrow  
        output : calendar  
        -----------------------
        input : Schedule a meeting at 3 PM  
        output : calendar  
        -----------------------
        input : Can you register a schedule for me?  
        output : calendar  
        -----------------------
        input : I want to change my appointment  
        output : calendar  
        -----------------------
        input : I have a lunch appointment tomorrow  
        output : calendar  
        -----------------------
        input : There’s a team dinner this Friday  
        output : calendar  
        -----------------------
        input : Check my schedule  
        output : calendar  
        -----------------------
        input : I’d like to add a new event  
        output : calendar  
        -----------------------
        input : Set up a reminder for next Monday  
        output : calendar  
        -----------------------
        input : Add an event to my calendar  
        output : calendar  
        -----------------------
        input : I have a plan tomorrow  
        output : calendar  
        -----------------------
        input : Schedule a meeting at 3 PM  
        output : calendar  
        -----------------------
        input : Can you register a schedule for me?  
        output : calendar  
        -----------------------
        input : I want to change my appointment  
        output : calendar  
        -----------------------
        input : I have a lunch appointment tomorrow  
        output : calendar  
        -----------------------
        input : There’s a team dinner this Friday  
        output : calendar  
        -----------------------
        input : Check my schedule  
        output : calendar  
        -----------------------
        input : I’d like to add a new event  
        output : calendar  
        -----------------------
        input : Set up a reminder for next Monday  
        output : calendar  
        -----------------------
        input : Add an event to my calendar  
        output : calendar  
        -----------------------
        input : I have a plan tomorrow  
        output : calendar  
        -----------------------
        input : Schedule a meeting at 3 PM  
        output : calendar  
        -----------------------
        input : Can you register a schedule for me?  
        output : calendar  
        -----------------------
        input : I want to change my appointment  
        output : calendar  
        -----------------------
        input : I have a lunch appointment tomorrow  
        output : calendar  
        -----------------------
        input : There’s a team dinner this Friday  
        output : calendar  
        -----------------------
        input : Check my schedule  
        output : calendar  
        -----------------------
        input : I’d like to add a new event  
        output : calendar  
        -----------------------
        input : Set up a reminder for next Monday  
        output : calendar  
        -----------------------
        input : Add an event to my calendar  
        output : calendar  
        -----------------------
        input : I have a plan tomorrow  
        output : calendar  
        -----------------------
        input : Schedule a meeting at 3 PM  
        output : calendar  
        -----------------------
        input : Can you register a schedule for me?  
        output : calendar  
        -----------------------
        input : I want to change my appointment  
        output : calendar  
        -----------------------
        input : I have a lunch appointment tomorrow  
        output : calendar  
        -----------------------
        input : There’s a team dinner this Friday  
        output : calendar  
        -----------------------
        input : Check my schedule  
        output : calendar  
        -----------------------
        input : I’d like to add a new event  
        output : calendar  
        -----------------------
        input : Set up a reminder for next Monday  
        output : calendar  
        -----------------------
        input : Add an event to my calendar  
        output : calendar  
        -----------------------
        input : I have a plan tomorrow  
        output : calendar  
        -----------------------
        input : Schedule a meeting at 3 PM  
        output : calendar  
        -----------------------
        input : Can you register a schedule for me?  
        output : calendar  
        -----------------------
        input : I want to change my appointment  
        output : calendar  
        -----------------------
        input : I have a lunch appointment tomorrow  
        output : calendar  
        -----------------------
        input : There’s a team dinner this Friday  
        output : calendar  
        -----------------------
        input : Check my schedule  
        output : calendar  
        -----------------------
        input : I’d like to add a new event  
        output : calendar  
        -----------------------
        input : Set up a reminder for next Monday  
        output : calendar  
        ----------------------- 
        input : I want to write about iMac
        output : post 
        -----------------------    
        input : Create a post for me  
        output : post  
        -----------------------
        input : I want to publish a blog article  
        output : post  
        -----------------------
        input : I’ll write a new post  
        output : post  
        -----------------------
        input : I’m starting to write a post  
        output : post  
        -----------------------
        input : I’d like to upload a post  
        output : post  
        -----------------------
        input : I’ll leave a message on the board  
        output : post  
        -----------------------
        input : Please turn the following into a post  
        output : post  
        -----------------------
        input : Here’s the content for the bulletin board  
        output : post  
        -----------------------
        input : I’m uploading a short post  
        output : post
        ----------------------- 
        input : I want to write about iMac
        output : post   
        -----------------------
        input : Please write a notice for users  
        output : post  
        -----------------------
        input : Create a post for me  
        output : post  
        -----------------------
        input : I want to publish a blog article  
        output : post  
        -----------------------
        input : I’ll write a new post  
        output : post  
        -----------------------
        input : I’m starting to write a post  
        output : post  
        -----------------------
        input : I’d like to upload a post  
        output : post  
        ----------------------- 
        input : I want to write about iMac
        output : post 
        -----------------------
        input : I’ll leave a message on the board  
        output : post  
        -----------------------
        input : Please turn the following into a post  
        output : post
        ----------------------- 
        input : I want to write about iMac
        output : post   
        -----------------------
        input : Here’s the content for the bulletin board  
        output : post  
        ----------------------- 
        input : I want to write about iMac
        output : post 
        -----------------------
        input : I’m uploading a short post  
        output : post  
        -----------------------
        input : Please write a notice for users  
        output : post  
        -----------------------
        input : Create a post for me  
        output : post  
        -----------------------
        input : I want to publish a blog article  
        output : post  
        -----------------------
        input : I’ll write a new post  
        output : post  
        -----------------------
        input : I’m starting to write a post  
        output : post  
        -----------------------
        input : I’d like to upload a post  
        output : post  
        -----------------------
        input : I’ll leave a message on the board  
        output : post  
        -----------------------
        input : Please turn the following into a post  
        output : post  
        -----------------------
        input : Here’s the content for the bulletin board  
        output : post  
        -----------------------
        input : I’m uploading a short post  
        output : post  
        -----------------------
        input : Please write a notice for users  
        output : post  
        -----------------------
        input : Create a post for me  
        output : post  
        -----------------------
        input : I want to publish a blog article  
        output : post  
        -----------------------
        input : I’ll write a new post  
        output : post  
        -----------------------
        input : I’m starting to write a post  
        output : post  
        -----------------------
        input : I’d like to upload a post  
        output : post  
        -----------------------
        input : I’ll leave a message on the board  
        output : post  
        -----------------------
        input : Please turn the following into a post  
        output : post  
        -----------------------
        input : Here’s the content for the bulletin board  
        output : post  
        -----------------------
        input : I’m uploading a short post  
        output : post  
        -----------------------
        input : Please write a notice for users  
        output : post  
        -----------------------
        input : Create a post for me  
        output : post  
        -----------------------
        input : I want to publish a blog article  
        output : post  
        -----------------------
        input : I’ll write a new post  
        output : post  
        -----------------------
        input : I’m starting to write a post  
        output : post  
        -----------------------
        input : I’d like to upload a post  
        output : post  
        -----------------------
        input : I’ll leave a message on the board  
        output : post  
        -----------------------
        input : Please turn the following into a post  
        output : post  
        -----------------------
        input : Here’s the content for the bulletin board  
        output : post  
        -----------------------
        input : I’m uploading a short post  
        output : post  
        -----------------------
        input : Please write a notice for users  
        output : post  
        -----------------------
        input : Create a post for me  
        output : post  
        -----------------------
        input : I want to publish a blog article  
        output : post  
        -----------------------
        input : I’ll write a new post  
        output : post  
        -----------------------
        input : I’m starting to write a post  
        output : post  
        -----------------------
        input : I’d like to upload a post  
        output : post  
        -----------------------
        input : I’ll leave a message on the board  
        output : post  
        -----------------------
        input : Please turn the following into a post  
        output : post  
        -----------------------
        input : Here’s the content for the bulletin board  
        output : post  
        -----------------------
        input : I’m uploading a short post  
        output : post  
        -----------------------
        input : Please write a notice for users  
        output : post  
        -----------------------
        input : all Other query
        output : general
        -----------------
        input : I want to create my resume  
        output : resume  
        ----------------
        input : Can you help me write a CV?  
        output : resume  
        ----------------
        input : 이력서를 작성하고 싶어  
        output : resume  
        ----------------
        input : 내 경력사항을 정리해줘  
        output : resume  
        ---------------
        input : What should I include in my resume for a developer role?  
        output : resume  
        ---------------
        input : 자기소개서나 경력기술서 필요해  
        output : resume  
        ---------------
        input : I need to update my resume for a job application  
        output : resume  
        ---------------
        input : I want to create my resume  
        output : resume  
        ---------------
        input : Can you help me write a CV?  
        output : resume  
        ---------------
        input : 이력서를 작성하고 싶어  
        output : resume  
        ---------------
        input : 내 경력사항을 정리해줘  
        output : resume  
        ---------------
        input : What should I include in my resume for a developer role?  
        output : resume  
        ---------------
        input : 자기소개서나 경력기술서 필요해  
        output : resume  
        ---------------
        input : I need to update my resume for a job application  
        output : resume  
        ---------------
        input : I want to create my resume  
        output : resume  
        ----------------
        input : Can you help me write a CV?  
        output : resume  
        ----------------
        input : 이력서를 작성하고 싶어  
        output : resume  
        ----------------
        input : 내 경력사항을 정리해줘  
        output : resume  
        ---------------
        input : What should I include in my resume for a developer role?  
        output : resume  
        ---------------
        input : 자기소개서나 경력기술서 필요해  
        output : resume  
        ---------------
        input : I need to update my resume for a job application  
        output : resume  
        ---------------
        input : I want to create my resume  
        output : resume  
        ---------------
        input : Can you help me write a CV?  
        output : resume  
        ---------------
        input : 이력서를 작성하고 싶어  
        output : resume  
        ---------------
        input : 내 경력사항을 정리해줘  
        output : resume  
        ---------------
        input : What should I include in my resume for a developer role?  
        output : resume  
        ---------------
        input : 자기소개서나 경력기술서 필요해  
        output : resume  
        ---------------
        input : I need to update my resume for a job application  
        output : resume  
        ---------------
        -----------------
        input : I want to create my resume  
        output : resume  
        ----------------
        input : Can you help me write a CV?  
        output : resume  
        ----------------
        input : 이력서를 작성하고 싶어  
        output : resume  
        ----------------
        input : 내 경력사항을 정리해줘  
        output : resume  
        ---------------
        input : What should I include in my resume for a developer role?  
        output : resume  
        ---------------
        input : 자기소개서나 경력기술서 필요해  
        output : resume  
        ---------------
        input : I need to update my resume for a job application  
        output : resume  
        ---------------
        input : I want to create my resume  
        output : resume  
        ---------------
        input : Can you help me write a CV?  
        output : resume  
        ---------------
        input : 이력서를 작성하고 싶어  
        output : resume  
        ---------------
        input : 내 경력사항을 정리해줘  
        output : resume  
        ---------------
        input : What should I include in my resume for a developer role?  
        output : resume  
        ---------------
        input : 자기소개서나 경력기술서 필요해  
        output : resume  
        ---------------
        input : I need to update my resume for a job application  
        output : resume  
        ---------------
        input : I want to create my resume  
        output : resume  
        ----------------
        input : Can you help me write a CV?  
        output : resume  
        ----------------
        input : 이력서를 작성하고 싶어  
        output : resume  
        ----------------
        input : 내 경력사항을 정리해줘  
        output : resume  
        ---------------
        input : What should I include in my resume for a developer role?  
        output : resume  
        ---------------
        input : 자기소개서나 경력기술서 필요해  
        output : resume  
        ---------------
        input : I need to update my resume for a job application  
        output : resume  
        ---------------
        input : I want to create my resume  
        output : resume  
        ---------------
        input : Can you help me write a CV?  
        output : resume  
        ---------------
        input : 이력서를 작성하고 싶어  
        output : resume  
        ---------------
        input : 내 경력사항을 정리해줘  
        output : resume  
        ---------------
        input : What should I include in my resume for a developer role?  
        output : resume  
        ---------------
        input : 자기소개서나 경력기술서 필요해  
        output : resume  
        ---------------
        input : I need to update my resume for a job application  
        output : resume  
        ---------------


        default.Respond only in JSON format
        
        """

        return prompt
    
    @staticmethod
    def make_html_ai_prompt():
        prompt = f""" 
        1. Please fill in the user information accordingly.
        2. ⚠️ Do NOT include any explanation or message. ONLY return a valid JSON object. No natural language..

        default. Please return 
        "html" : html
        
        [java script]
        -----------
        today = date.today()
        today_str = f" today.year 년  today.month:02d 월  today.day:02d 일"

        # 가족사항 3줄 생성 (빈 줄 포함)
        family_rows = user_data.get('family', [])
        family_rows = (family_rows + [] * 3)[:3]  # 최대 3줄로 제한
        family_html = ''
        family_html += '''
            <tr>
                <td rowspan="4">가족관계</td>
                <td>관 계</td>
                <td>성 명</td>
                <td colspan="2">연 령</td>
                <td colspan="2">현재직업</td>
            </tr>
        '''
        for row in family_rows:
            family_html += f'''	
            <tr>
                <td>row.get('relation', '')</td>
                <td>row.get('name', '')</td>
                <td colspan="2">row.get('age', '')</td>
                <td colspan="2">row.get('job', '')</td>
            </tr>
            '''

        # 학력/자격사항 5개 row 생성
        education_rows = user_data.get('education', [])
        certifications_rows = user_data.get('certifications', [])
        edu_cert_rows = education_rows + certifications_rows
        edu_cert_rows = (edu_cert_rows + [] * 5)[:5]
        edu_cert_html = ''.join([
            f'''<tr>\n<td class="period-cell">row.get('period', '')</td>\n<td class="content-cell">row.get('school', row.get('name', '')) row.get('major', '') row.get('degree', '') row.get('issuer', '') row.get('grade', '')</td>\n<td class="note-cell"></td>\n</tr>''' for row in edu_cert_rows
        ])

        # 경력사항 5개 row 생성
        career_rows = user_data.get('career', [])
        career_rows = (career_rows + [] * 5)[:5]
        career_html = ''.join([
            f'''<tr>\n<td class="period-cell">row.get('period', '')</td>\n<td class="content-cell">row.get('company', '') row.get('position', '')</td>\n<td class="note-cell">row.get('description', '')</td>\n</tr>''' for row in career_rows
        ])

        [HTML FORM]
        -------------------
        <!DOCTYPE html>
        <html lang="ko">
        <head>
            <meta charset="UTF-8">
            <style>
                @page
                    size: A4;
                    margin: 0;

                body
                    font-family: 'Batang', serif;
                    margin: 0;
                    padding: 0;
                    line-height: 1.5;

                .page
                    width: 210mm;
                    height: 297mm;
                    padding: 15mm 20mm;
                    box-sizing: border-box;

                h1
                    text-align: center;
                    font-size: 24px;
                    margin-bottom: 10px;
                    letter-spacing: 15px;
                    font-weight: normal;

                table
                    width: 100%;
                    border-collapse: collapse;
                    margin-bottom: 20px;
                    font-size: 11px;

                th, td
                    border: 1.2px solid black;
                    padding: 8px 4px;
                    text-align: center;
                    vertical-align: middle;
                    height: 25px;
                    box-sizing: border-box;

                .photo-cell
                    width: 30mm;
                    height: 40mm;
                    text-align: center;
                    vertical-align: middle;
                    font-size: 10px;
                    color: #666;

                .header-table td
                    height: 32px;

                .family-table td
                    height: 28px;

                .period-cell
                    width: 20%;

                .content-cell
                    width: 60%;

                .note-cell
                    width: 20%;

                .footer
                    margin-top: 60px;
                    text-align: center;
                    font-size: 12px;

                .date-line
                    margin: 30px 0;
                    line-height: 2;
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
                        <td colspan="2">홍길동</td>
                        <td colspan="2">생년월일</td>
                        <td colspan="2">1990-01-01</td>
                    </tr>
                    <tr>
                        <td>전화번호</td>
                        <td colspan="2">010-1234-5678</td>
                        <td colspan="2">국적</td>
                        <td>대한민국</td>
                    </tr>
                    <tr>
                        <td rowspan="4">가족관계</td>
                        <td>관 계</td>
                        <td>성 명</td>
                        <td colspan="2">연 령</td>
                        <td colspan="2">현재직업</td>
                    </tr>
                    <tr>
                        <td>부</td>
                        <td>홍아버지</td>
                        <td colspan="2">65</td>
                        <td colspan="2">자영업</td>
                    </tr>
                    <tr>
                        <td>모</td>
                        <td>홍어머니</td>
                        <td colspan="2">60</td>
                        <td colspan="2">주부</td>
                    </tr>
                    <tr>
                        <td>형제</td>
                        <td>홍동생</td>
                        <td colspan="2">30</td>
                        <td colspan="2">회사원</td>
                    </tr>
                    <tr>
                        <td colspan="2">현 주 소</td>
                        <td colspan="5">서울시 강남구</td>
                    </tr>
                    <tr>
                        <td colspan="2">이메일</td>
                        <td colspan="5">hong@example.com</td>
                    </tr>
                </table>

                <table>
                    <tr>
                        <th class="period-cell">기 간</th>
                        <th class="content-cell">학 력 · 자 격 사 항</th>
                        <th class="note-cell">비 고</th>
                    </tr>
                    <tr>
                        <td>2010-2014</td>
                        <td>서울대학교 컴퓨터공학과 학사</td>
                        <td></td>
                    </tr>
                    <tr>
                        <td>2015</td>
                        <td>정보처리기사 자격증</td>
                        <td></td>
                    </tr>
                </table>

                <table>
                    <tr>
                        <th class="period-cell">기 간</th>
                        <th class="content-cell">경 력 사 항</th>
                        <th class="note-cell">비 고</th>
                    </tr>
                    <tr>
                        <td>2016-2018</td>
                        <td>네이버 소프트웨어 엔지니어</td>
                        <td>검색 엔진 개발</td>
                    </tr>
                    <tr>
                        <td>2018-2023</td>
                        <td>카카오 시니어 개발자</td>
                        <td>메시징 플랫폼 개발</td>
                    </tr>
                </table>

                <div class="footer">
                    <p>위의 기재한 내용이 사실과 다름이 없습니다.</p>
                    <div class="date-line">
                        2025년 05월 14일
                    </div>
                    <p>(인)</p>
                </div>
            </div>
        </body>
        </html>


        """
       

        return prompt