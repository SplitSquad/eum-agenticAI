import httpx  # ✅ 비동기 요청 라이브러리

class User_Api:
    def __init__(self):
        self.base_url = "https://api.eum-friends.com"

    async def user_api(self, token: str):
        url = f"{self.base_url}/users/profile"
        headers = {
            "Authorization": token,  # ✅ Bearer 붙이기
            "Content-Type": "application/json"
        }

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                print("✅ 사용자 정보 가져오기 성공")
                return response.json()
            except httpx.HTTPStatusError as e:
                print(f"❌ 요청 실패: {e.response.status_code}")
                print("💬 응답 내용:", e.response.text)
                return {"error": e.response.text}
            except Exception as e:
                print(f"🚨 기타 오류: {str(e)}")
                return {"error": str(e)}

    async def user_prefer_api(self, token: str):
        url = f"{self.base_url}/users/preference"
        headers = {
            "Authorization": token,  # ✅ Bearer 붙이기
            "Content-Type": "application/json"
        }

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                print("✅ 사용자 정보 가져오기 성공")
                return response.json()
            except httpx.HTTPStatusError as e:
                print(f"❌ 요청 실패: {e.response.status_code}")
                print("💬 응답 내용:", e.response.text)
                return {"error": e.response.text}
            except Exception as e:
                print(f"🚨 기타 오류: {str(e)}")
                return {"error": str(e)}
