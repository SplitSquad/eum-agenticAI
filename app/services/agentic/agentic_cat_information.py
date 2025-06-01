import aiohttp
import os
import uuid
import asyncio
from loguru import logger
from app.core.llm_client import dalle
from app.config import s3_config
import aiofiles.tempfile as tempfile
import aiofiles
import boto3

class Cat_Infromation:
    def __init__(self): 
        self.url = "https://catfact.ninja/fact"
        self.bucket = s3_config.S3_BUCKET_NAME
        self.region = s3_config.S3_REGION
        self.client = boto3.client(
            "s3",
            aws_access_key_id=s3_config.S3_ACCESS_KEY,
            aws_secret_access_key=s3_config.S3_SECRET_KEY,
            region_name=s3_config.S3_REGION
        )

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
        response = await self.img_to_s3(image_url)
        return response
    
    async def img_to_s3(self, image_url: str) -> str:
        logger.info(f"[이미지 다운로드 시작] : {image_url}")
        async with aiohttp.ClientSession() as session:
            async with session.get(image_url) as response:
                if response.status != 200:
                    raise Exception(f"Image download failed: {response.status}")

                tmp_path=""
                # 임시 파일에 저장
                async with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_file:
                    content = await response.read()
                    await tmp_file.write(content)
                    tmp_path = tmp_file.name

        # S3 업로드 경로 설정
        filename = f"{uuid.uuid4().hex}.png"
        key = f"cats/{filename}"

        try:
            self.client.upload_file(
                tmp_path,
                self.bucket,
                key,
                ExtraArgs={"ContentType": "image/png"},
            )
        finally:
            os.remove(tmp_path)  # 임시 파일 삭제

        s3_url = f"https://{self.bucket}.s3.{self.region}.amazonaws.com/{key}"
        logger.info(f"✅ S3 업로드 완료: {s3_url}")

        # 선택적으로 삭제 예약
        asyncio.create_task(self.schedule_deletion(key, delay_sec=600))

        return s3_url

    async def schedule_deletion(self, key: str, delay_sec: int = 600):
        await asyncio.sleep(delay_sec)
        try:
            self.client.delete_object(Bucket=self.bucket, Key=key)
            logger.info(f"🗑️ S3 파일 삭제 완료: {key}")
        except Exception as e:
            logger.error(f"S3 삭제 실패: {e}")
