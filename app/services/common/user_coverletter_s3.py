import asyncio
import boto3
import os
from loguru import logger
from app.config import s3_config

class UserCoverLetterS3:
    def __init__(self):
        self.bucket = s3_config.S3_BUCKET_NAME
        self.client = boto3.client(
            "s3",
            aws_access_key_id=s3_config.S3_ACCESS_KEY,
            aws_secret_access_key=s3_config.S3_SECRET_KEY,
            region_name=s3_config.S3_REGION
        )

    async def upload_pdf(self, pdf_path: str) -> str:
        key = f"coverletters/{os.path.basename(pdf_path)}"
        self.client.upload_file(pdf_path, self.bucket, key)
        url = f"https://{self.bucket}.s3.{s3_config.S3_REGION}.amazonaws.com/{key}"
        logger.info(f"✅ [자소서] S3 업로드 완료: {url}")
        asyncio.create_task(self.schedule_deletion(key, delay_sec=600))
        return url

    async def schedule_deletion(self, key: str, delay_sec: int = 600):
        logger.info(f"⏳ [자소서] {delay_sec}초 후 {key} 삭제 예약됨")
        await asyncio.sleep(delay_sec)
        try:
            self.client.delete_object(Bucket=self.bucket, Key=key)
            logger.info(f"🗑️ [자소서] S3 객체 삭제 완료: {key}")
        except Exception as e:
            logger.error(f"❌ [자소서] S3 객체 삭제 실패: {e}") 