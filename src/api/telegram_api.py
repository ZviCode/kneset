import requests
from typing import List, Dict, Any
import io
from utils.logger import logger
from config import TELEGRAM_API, CHANNEL_ID
from PIL import Image


class TelegramAPI:
    def __init__(self):
        """Initialize TelegramAPI with ImageService."""
        from services.image_service import ImageService
        self.image_service = ImageService()

    @staticmethod
    def _image_to_bytes(image: Image.Image) -> bytes:
        """Convert PIL Image to bytes."""
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format='JPEG', quality=95)
        img_byte_arr.seek(0)
        return img_byte_arr.getvalue()

    async def send_photo(self, members_data: List[Dict[str, Any]], caption: str):
        """Send photo with present members to Telegram."""
        try:
            # Filter for present members only
            present_members = [m for m in members_data if m['IsPresent']]

            # Create image using ImageService
            image = await self.image_service.create_presence_image(present_members)
            if image is None:
                logger.error("Failed to create presence image")
                return None

            # Convert image to bytes
            image_bytes = self._image_to_bytes(image)

            files = {
                'photo': ('presence.jpg', image_bytes, 'image/jpeg'),
            }

            data = {
                'chat_id': CHANNEL_ID,
                'caption': caption,
                'parse_mode': 'HTML'
            }

            response = requests.post(
                f"{TELEGRAM_API}/sendPhoto",
                data=data,
                files=files
            )

            if response.status_code == 200:
                result = response.json()
                if result.get('ok'):
                    return result['result']['message_id']
                else:
                    logger.error(f"Telegram API returned not OK: {result}")
                    return None

            logger.error(f"Error sending photo: {response.text}")
            return None

        except Exception as e:
            logger.error(f"Error sending photo: {e}")
            logger.exception("Full traceback:")
            return None

    async def update_caption(self, message_id: int, caption: str) -> bool:
        """Update caption of existing message."""
        try:
            if not message_id:
                logger.error("Invalid message_id: cannot be None or empty")
                return False

            data = {
                'chat_id': CHANNEL_ID,
                'message_id': message_id,
                'caption': caption,
                'parse_mode': 'HTML'
            }

            response = requests.post(
                f"{TELEGRAM_API}/editMessageCaption",
                data=data
            )

            if response.status_code == 200:
                result = response.json()
                if not result.get('ok'):
                    logger.error(f"Telegram API returned not OK: {result}")
                    return False
                return True

            logger.error(f"Error updating caption. Status code: {response.status_code}, Response: {response.text}")
            return False

        except Exception as e:
            logger.error(f"Error updating caption: {e}")
            return False