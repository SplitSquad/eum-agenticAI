import reverse_geocoder as rg
from loguru import logger
import requests

class search_location():
    def __init__(self):
        self.coordinates = ()
        self.result = ""

    # def search(self, location):
    #     # location.latitude, location.longitude 는 float 타입이어야 합니다.
    #     self.coordinates = (float(location.latitude), float(location.longitude))
    #     self.result = rg.search([self.coordinates])
    #     logger.info(f"[location_result] : {self.result}")
    #     return self.result
    
    def search(self, location) -> dict:
        url = "https://dapi.kakao.com/v2/local/geo/coord2address.json"
        headers = {
            "Authorization": f"KakaoAK 5d96c7a6ef9ac4662396eafc9c44f63e"
        }
        try:
            x = float(location.longitude)
            y = float(location.latitude)
        except (AttributeError, ValueError, TypeError) as e:
            logger.error(f"Invalid location data: {e}")
            return {}

        params = {
            "x": x,
            "y": y,
            "input_coord": "WGS84"
        }

        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()
            if data.get('documents'):
                return data['documents'][0]
            else:
                logger.warning("No address information found for the given coordinates.")
                return {}
        except requests.RequestException as e:
            logger.error(f"Request failed: {e}")
            return {}
