import aiohttp
import os
from loguru import logger
from openai import AsyncOpenAI
from dotenv import load_dotenv

load_dotenv()  # .env 파일에서 OPENAI_API_KEY 로드

client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class RandomDog:
    def __init__(self):
        self.url = "https://dog.ceo/api/breeds/image/random"

    async def api_random_image(self):
        logger.info("[api_random_image...]")
        async with aiohttp.ClientSession() as session:
            async with session.get(self.url) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"[data] : {data}")
                    return data  # {'message': 'image_url', 'status': 'success'}
                else:
                    return {"error": f"Failed to fetch image. Status code: {response.status}"}

    async def describe_img(self, image_url: str):
        logger.info("[describe...]")
        response = await client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "이 강아지 이미지를 설명해줘."},
                        {"type": "image_url", "image_url": {"url": image_url}}
                    ]
                }
            ],
            max_tokens=300
        )
        return response.choices[0].message.content
