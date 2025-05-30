import reverse_geocoder as rg
from loguru import logger

class search_location():
    def __init__(self):
        self.coordinates = ()
        self.result = ""

    def search(self, location):
        # location.latitude, location.longitude 는 float 타입이어야 합니다.
        self.coordinates = (float(location.latitude), float(location.longitude))
        self.result = rg.search([self.coordinates])
        logger.info(f"[location_result] : {self.result}")
        return self.result
