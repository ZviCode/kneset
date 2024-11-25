import io
from typing import List, Dict, Any, Optional
from PIL import Image, ImageDraw, ImageFont
import requests
from utils.logger import logger
from utils.text_utils import reverse_hebrew_text, hebrew_sort_key
from config import CACHE_DIR, FONT_PATH, FONT_SIZE


class ImageService:
    def __init__(self):
        """Initialize ImageService with font and cache directory."""
        self.font = self._load_font()
        CACHE_DIR.mkdir(exist_ok=True)

        # Image configuration
        self.width = 800
        self.img_size = 180
        self.spacing = 20
        self.members_per_row = 4
        self.background_color = (220, 240, 255, 255)

    def _load_font(self) -> ImageFont.FreeTypeFont:
        """Load the font for image text."""
        try:
            return ImageFont.truetype(str(FONT_PATH), FONT_SIZE)
        except Exception as e:
            logger.warning(f"Failed to load Arial font: {e}")
            return ImageFont.load_default()

    async def download_member_image(self, url: str) -> Optional[Image.Image]:
        """
        Download and cache member image from URL.

        Args:
            url: URL of the member's image

        Returns:
            Optional[Image.Image]: PIL Image object or None if download fails
        """
        try:
            if not url:
                return None

            cache_key = str(hash(url)) + ".jpg"
            cache_path = CACHE_DIR / cache_key

            if cache_path.exists():
                return Image.open(cache_path)

            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }

            response = requests.get(url, headers=headers, verify=False)
            if response.status_code == 200:
                image = Image.open(io.BytesIO(response.content))
                image.save(cache_path)
                return image

            logger.warning(f"Failed to download image from {url}: {response.status_code}")
            return None

        except Exception as e:
            logger.error(f"Error downloading image from {url}: {e}")
            return None

    def _calculate_image_dimensions(self, total_members: int) -> tuple[int, int]:
        """Calculate the dimensions for the final image based on member count."""
        row_height = self.img_size + FONT_SIZE + self.spacing
        num_rows = (total_members + self.members_per_row - 1) // self.members_per_row
        height = num_rows * row_height
        return self.width, height

    def _get_member_position(self, index: int, total_members: int,
                             num_rows: int) -> tuple[int, int]:
        """Calculate x, y position for member image and text."""
        current_row = index // self.members_per_row
        is_last_row = current_row == num_rows - 1
        column_in_row = index % self.members_per_row

        row_height = self.img_size + FONT_SIZE + self.spacing
        y = current_row * row_height + self.spacing

        if is_last_row:
            total_in_row = min(self.members_per_row,
                               total_members - (current_row * self.members_per_row))
            offset = (self.members_per_row - total_in_row) * (self.width // self.members_per_row) // 2
            x = column_in_row * (self.width // self.members_per_row) + offset
        else:
            x = (self.members_per_row - 1 - column_in_row) * (self.width // self.members_per_row)

        return x + self.spacing, y

    def _draw_member_name(self, draw: ImageDraw.ImageDraw, member: Dict[str, Any],
                          x: int, y: int) -> None:
        """Draw member name."""
        lastname = reverse_hebrew_text(member['Lastname'])
        firstname = reverse_hebrew_text(member['Firstname'])
        name = f"{lastname} {firstname}"

        bbox = self.font.getbbox(name)
        text_width = bbox[2] - bbox[0]

        text_x = x + (self.img_size - text_width) // 2
        text_y = y + self.img_size

        # Draw text without shadow
        draw.text((text_x, text_y), name, fill=(0, 0, 0), font=self.font)

    async def create_presence_image(self, present_members: List[Dict[str, Any]]) -> Optional[Image.Image]:
        """
        Create image with present Knesset members.

        Args:
            present_members: List of dictionaries containing member data

        Returns:
            Optional[Image.Image]: PIL Image object or None if creation fails
        """
        try:
            sorted_members = sorted(present_members, key=hebrew_sort_key)
            width, height = self._calculate_image_dimensions(len(sorted_members))
            num_rows = (len(sorted_members) + self.members_per_row - 1) // self.members_per_row

            # Create base image
            image = Image.new('RGBA', (width, height), self.background_color)
            draw = ImageDraw.Draw(image)

            for i, member in enumerate(sorted_members):
                try:
                    member_img = await self.download_member_image(member['ImagePath'])
                    if member_img is None:
                        continue

                    # Resize and convert image
                    member_img = member_img.resize((self.img_size, self.img_size))
                    if member_img.mode != 'RGBA':
                        member_img = member_img.convert('RGBA')

                    # Calculate position and paste image
                    x, y = self._get_member_position(i, len(sorted_members), num_rows)
                    image.paste(member_img, (x, y),
                                member_img if member_img.mode == 'RGBA' else None)

                    # Draw member name
                    self._draw_member_name(draw, member, x, y)

                except Exception as e:
                    logger.error(f"Error processing member {member.get('Lastname', 'Unknown')}: {e}")
                    continue

            # Convert to RGB for final output
            rgb_image = Image.new('RGB', image.size, (255, 255, 255))
            rgb_image.paste(image, mask=image.split()[3])

            return rgb_image

        except Exception as e:
            logger.error(f"Error creating presence image: {e}")
            return None