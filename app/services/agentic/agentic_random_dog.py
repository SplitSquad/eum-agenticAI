import aiohttp

class RandomDog:
    def __init__(self):
        self.url = "https://dog.ceo/api/breeds/image/random"

    async def api_random_image(self):
        async with aiohttp.ClientSession() as session:
            async with session.get(self.url) as response:
                if response.status == 200:
                    data = await response.json()
                    return data  # {'message': 'image_url', 'status': 'success'}
                else:
                    return {"error": f"Failed to fetch image. Status code: {response.status}"}
