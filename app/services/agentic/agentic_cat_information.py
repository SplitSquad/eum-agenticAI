import aiohttp
import os
from loguru import logger
from app.core.llm_client import dalle


class Cat_Infromation:
    def __init__(self): 
        self.url = "https://catfact.ninja/fact"

    async def hidden_cat_information(self):
        logger.info("[hidden_cat_information_search...]")
        async with aiohttp.ClientSession() as session:
            async with session.get(self.url) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"[data] : {data}")
                    return data  # {"fact": "The first true cats came into existence about 12 million years ago and were the Proailurus.","length": 91}
                else:
                    return {"error": f"Failed to fetch image. Status code: {response.status}"}
                
    async def describe_img(self, describe_text):
        image_url = await dalle(describe_text)
        return image_url
