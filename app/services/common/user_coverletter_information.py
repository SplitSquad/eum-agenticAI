import os
import json
from typing import Any

class UserCoverLetterInformation:
    def __init__(self, storage_dir: str = "data_coverletter"):
        self.storage_dir = storage_dir
        os.makedirs(self.storage_dir, exist_ok=True)

    async def store_user_data(self, uid: str, query: str, state: str,intend:str):
        file_path = os.path.join(self.storage_dir, f"{uid}.json")
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        else:
            data = {"uid": uid}
        data[state] = query
         # 📌 추가: 사용자의 의도(intend)도 저장
        data["intend"] = intend
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        print(f"✅ [자소서] 상태 [{state}] 저장 완료: {file_path}")

    async def delete_user_data(self, uid: str):
        file_path = os.path.join(self.storage_dir, f"{uid}.json")
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"🗑️ [자소서] 삭제 완료: {file_path}")
        else:
            print(f"⚠️ [자소서] 파일 없음: {file_path}")

    async def all(self, uid: str):
        file_path = os.path.join(self.storage_dir, f"{uid}.json")
        if not os.path.exists(file_path):
            print(f"⚠️ [자소서] 파일 없음: {file_path}")
            return {}
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        print(f"📄 [자소서] UID: {uid} - 저장된 상태 목록")
        for key, value in data.items():
            if key != "uid":
                print(f"🟢 상태: {key} → 질문: {value}")
        result = {key: value for key, value in data.items() if key != "uid"}
        return result 