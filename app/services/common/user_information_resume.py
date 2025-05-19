import os
import json
from typing import Any

class User_Information_Resume:
    def __init__(self, storage_dir: str = "data"):
        self.storage_dir = storage_dir
        os.makedirs(self.storage_dir, exist_ok=True)

    async def store_user_data(self, uid: str, query: str, state: str):
        """
        UID에 해당하는 JSON 파일을 저장하거나 상태별로 업데이트
        """
        file_path = os.path.join(self.storage_dir, f"{uid}.json")
        
        # 기존 데이터가 있으면 불러오기
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        else:
            data = {"uid": uid}

        # 상태별 쿼리 업데이트
        data[state] = query

        # 저장
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

        print(f"✅ 상태 [{state}] 저장 완료: {file_path}")


    async def delete_user_data(self, uid: str):
        """
        UID에 해당하는 JSON 파일 삭제
        """
        file_path = os.path.join(self.storage_dir, f"{uid}.json")
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"🗑️ 삭제 완료: {file_path}")
        else:
            print(f"⚠️ 파일 없음: {file_path}")

    async def all(self, uid: str):
        """
        UID에 해당하는 모든 상태(state)와 쿼리(query) 출력
        """
        file_path = os.path.join(self.storage_dir, f"{uid}.json")

        if not os.path.exists(file_path):
            print(f"⚠️ 파일 없음: {file_path}")
            return {}

        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        print(f"📄 UID: {uid} - 저장된 상태 목록")
        for key, value in data.items():
            if key != "uid":
                print(f"🟢 상태: {key} → 질문: {value}")

        # "uid" 키는 제외하고 상태만 추출
        result = {key: value for key, value in data.items() if key != "uid"}

        return result


