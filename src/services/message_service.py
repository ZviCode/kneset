from collections import defaultdict
from datetime import datetime
from typing import List, Dict, Any, Tuple
import pytz
from utils.text_utils import format_rtl_text
from utils.logger import logger
from api.telegram_api import TelegramAPI


class MessageService:
    def __init__(self):
        """Initialize MessageService with TelegramAPI instance."""
        self.telegram = TelegramAPI()
        self.israel_tz = pytz.timezone('Asia/Jerusalem')

    @staticmethod
    def _get_emoji_for_percentage(percentage: float) -> str:
        """Return appropriate emoji based on attendance percentage."""
        if percentage >= 75:
            return "🟢"
        elif percentage >= 50:
            return "🟡"
        return "🟠"

    @staticmethod
    def _number_to_emoji(number: int) -> str:
        """Convert number to emoji representation."""
        number_emojis = {
            '0': '0️⃣', '1': '1️⃣', '2': '2️⃣', '3': '3️⃣', '4': '4️⃣',
            '5': '5️⃣', '6': '6️⃣', '7': '7️⃣', '8': '8️⃣', '9': '9️⃣'
        }
        return ''.join(number_emojis[d] for d in str(number))

    def _calculate_coalition_stats(self, members: List[Dict[str, Any]]) -> Tuple[int, int, int, int]:
        """Calculate coalition and opposition statistics."""
        coalition_present = opposition_present = 0
        coalition_total = opposition_total = 0

        for member in members:
            if member['IsCoalition']:
                coalition_total += 1
                if member['IsPresent']:
                    coalition_present += 1
            else:
                opposition_total += 1
                if member['IsPresent']:
                    opposition_present += 1

        return coalition_present, coalition_total, opposition_present, opposition_total

    def _calculate_faction_stats(self, present_members: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Calculate statistics for each faction."""
        faction_counts = defaultdict(int)
        faction_totals = defaultdict(int)

        for member in present_members:
            faction_name = member['FactionName']
            faction_totals[faction_name] += 1
            if member['IsPresent']:
                faction_counts[faction_name] += 1

        faction_data = []
        for faction, total in faction_totals.items():
            present = faction_counts[faction]
            if present > 0:  # רק סיעות עם נוכחים
                percentage = (present / total) * 100
                faction_data.append({
                    'name': faction,
                    'present': present,
                    'total': total,
                    'percentage': percentage
                })

        return sorted(faction_data, key=lambda x: (-x['percentage'], x['name']))

    def get_faction_summary(self, present_members: List[Dict[str, Any]]) -> str:
        """
        Generate a formatted summary of Knesset attendance by faction.

        Args:
            present_members: List of dictionaries containing member data

        Returns:
            str: Formatted message ready for Telegram
        """
        try:
            # Calculate coalition/opposition statistics
            coalition_present, coalition_total, opposition_present, opposition_total = \
                self._calculate_coalition_stats(present_members)

            # Calculate faction statistics
            faction_data = self._calculate_faction_stats(present_members)
            total_present = sum(f['present'] for f in faction_data)

            # Get current time in Israel timezone
            current_time = datetime.now(self.israel_tz).strftime("%H:%M")

            # Format faction lines
            faction_lines = []
            for faction in faction_data:
                indicator = self._get_emoji_for_percentage(faction['percentage'])
                line = f"{indicator} {faction['name']}: {faction['present']}/{faction['total']}"
                faction_lines.append(line)

            # Construct message parts
            message_parts = [
                format_rtl_text(f"🏛️ עדכון נוכחות במליאת הכנסת | {current_time}"),
                format_rtl_text("──────────────────"),
                format_rtl_text(f"👥 סה״כ חברי כנסת במליאה: {self._number_to_emoji(total_present)}"),
                "",
                format_rtl_text(f"🔷 קואליציה: {coalition_present}/{coalition_total}"),
                format_rtl_text(f"🔶 אופוזיציה: {opposition_present}/{opposition_total}"),
                "",
                format_rtl_text("📊 נוכחות לפי סיעות:"),
                format_rtl_text("\n".join(faction_lines)),
                "",
                format_rtl_text("🔄 מתעדכן כל דקה")
            ]

            return "\n".join(message_parts)

        except Exception as e:
            logger.error(f"Error generating faction summary: {e}")
            raise

    async def update_or_resend(self, last_message_id: int, present_members: List[Dict[str, Any]],
                               caption: str) -> int:
        """
        Try to update existing message, send new one if update fails.

        Args:
            last_message_id: ID of the last sent message
            present_members: List of member data dictionaries
            caption: Message caption to update or send

        Returns:
            int: Message ID of updated or new message
        """
        try:
            if not last_message_id:
                logger.info("No last message ID, sending new message")
                return await self.telegram.send_photo(present_members, caption)

            logger.info(f"Attempting to update message {last_message_id}")
            if await self.telegram.update_caption(last_message_id, caption):
                logger.info(f"Successfully updated message {last_message_id}")
                return last_message_id

            logger.warning(f"Failed to update message {last_message_id}, sending new message")
            return await self.telegram.send_photo(present_members, caption)

        except Exception as e:
            logger.error(f"Error in update_or_resend: {e}")
            return await self.telegram.send_photo(present_members, caption)