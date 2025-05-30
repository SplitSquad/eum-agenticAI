from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate
from app.core.llm_client import get_langchain_llm
from app.services.common.user_s3 import UserS3 
from loguru import logger
import os
import json
from dotenv import load_dotenv
from openai import AsyncOpenAI

load_dotenv()  # .env 파일에서 OPENAI_API_KEY 로드

client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class agentic_eum_image():
    def __init__(self):
        # 현재 파일 위치: app/services/agentic/agentic_eum_image.py
        # → 상위 두 단계 올라가서 app/services/common/eum-data-set 으로 접근
        base_dir = os.path.dirname(os.path.abspath(__file__))  # 현재 파일 기준 디렉토리
        self.image_path = os.path.normpath(
            os.path.join(base_dir, "..", "common", "eum-data-set")
        )
        print(f"[이미지 경로 확인] {self.image_path}")
        self.upload_s3 = UserS3()

    async def select_image(self,query):
        llm = get_langchain_llm(is_lightweight=False)  # 고성능 모델 사용

        parser = JsonOutputParser(pydantic_object={
            "type": "object",
            "properties": {
                "input": {"type": "string"},
                "output": {"type": "string"},
            }
        })

        # 프롬프트 문자열 구성
        system_prompt_template = f"""
        1. You are an AI that selects images that suit the user's needs.
        2. Please choose one of them.
        [
            "eum_default.png",
            "eum_default_2.png",
            "eum_fighting.png",
            "eum_fighting_hard.png",
            "eum_fist_cheering.png",
            "eum_greeting.png",
            "eum_happy.png",
            "eum_happy_run.png",
            "eum_jump.png",
            "eum_light_jump.png",
            "eum_point.png",
            "eum_run.png",
            "eum_catch_fairy_tale_style.png"
            "There_is_no_image "
        ]
        default. !! return type is json !! 

        [format]
        "output" : "..."

        [few-shot] : 
        "input" : "EUM's smiling face"
        "output" : "eum_happy.png"

        """

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt_template ),
            ("user", "{input}")
        ])

        chain = prompt | llm | parser

        def parse_product(description: str) -> dict:
            result = chain.invoke({"input": description})
            print(f"[AI_OUTPUT] : {json.dumps(result, indent=2, ensure_ascii=False)}")
            return result

        description = query

        response = parse_product(description)

        return response["output"]
    
    async def choose_img(self,selected_eum_image):
        local_image_path = os.path.join(self.image_path, selected_eum_image)
        uploaded_url = await self.upload_s3.upload_file(local_image_path, s3_folder="eum-images/")
        return uploaded_url
    
    async def describe_eum(self, image_url: str):
        logger.info("[describe...]")
        response = await client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": " Describe the character in the image , Additional information His name is EUM and he is a boy who loves Korean traditions. And he is the representative icon of our service. "},
                        {"type": "image_url", "image_url": {"url": image_url}}
                    ]
                }
            ],
            max_tokens=300
        )
        return response.choices[0].message.content