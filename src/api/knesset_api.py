import requests
import urllib3
from utils.logger import logger
from config import KNESSET_API_URL

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class KnessetAPI:
    @staticmethod
    async def fetch_data():
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'application/json',
                'Accept-Language': 'he-IL,he;q=0.9,en-US;q=0.8,en;q=0.7',
                'Referer': 'https://www.knesset.gov.il/',
                'Origin': 'https://www.knesset.gov.il'
            }
            
            response = requests.get(KNESSET_API_URL, headers=headers, verify=False)
            logger.info(f"Response status code: {response.status_code}")
            
            response.raise_for_status()
            data = response.json()
            
            logger.info(f"Successfully fetched data with {len(data.get('mks', []))} members")
            return data
            
        except Exception as e:
            logger.error(f"Error fetching Knesset data: {e}")
            return None