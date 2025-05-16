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

        return prompt
    

    @staticmethod
    def agentic_classifier_prompt():

        prompt = """
        1. Its role is to inform the category.
        2. Here is a few-shot example.
        -----------------------
        input : Add an event to my calendar  
        output : calendar  
        

        default.Respond only in JSON format
        
        """

        return prompt