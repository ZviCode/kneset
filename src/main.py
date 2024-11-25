import asyncio
from utils.logger import logger
from utils.state_manager import StateManager
from api.knesset_api import KnessetAPI
from api.telegram_api import TelegramAPI
from services.message_service import MessageService
from config import POLLING_INTERVAL, MAX_RETRIES
import time

async def main():
    state_manager = StateManager()
    knesset_api = KnessetAPI()
    message_service = MessageService()
    telegram_api = TelegramAPI()
    
    retries = 0
    last_message_id, previous_present_members = state_manager.load_state()
    
    logger.info(f"Starting Knesset attendance bot with last message ID: {last_message_id}")
    
    while True:
        try:
            start_time = time.time()
            data = await knesset_api.fetch_data()
            if not data:
                if retries < MAX_RETRIES:
                    retries += 1
                    logger.warning(f"Failed to fetch data. Retry {retries}/{MAX_RETRIES}")
                    await asyncio.sleep(POLLING_INTERVAL)
                    continue
                else:
                    logger.error("Max retries reached for data fetch")
                    break
                    
            retries = 0
            current_present = {member['MkId'] for member in data['mks'] if member['IsPresent']}
            caption = message_service.get_faction_summary(data['mks'])

            logger.info(f"Current present members: {len(current_present)}")
            logger.info(f"Previous present members: {len(previous_present_members)}")

            if current_present != previous_present_members:
                present_members = [m for m in data['mks'] if m['IsPresent']]
                logger.info(f"Change detected! Present members: {len(present_members)}")
                
                new_message_id = await telegram_api.send_photo(present_members, caption)
                if new_message_id:
                    last_message_id = new_message_id
                    previous_present_members = current_present
                    logger.info(f"Saving state with message ID: {last_message_id}")
                    state_manager.save_state(last_message_id, previous_present_members)
            else:
                logger.info("No change in presence, updating existing message")
                new_message_id = await message_service.update_or_resend(last_message_id, 
                                                  [m for m in data['mks'] if m['IsPresent']], 
                                                  caption)
                if new_message_id and new_message_id != last_message_id:
                    last_message_id = new_message_id
                    logger.info(f"Updating state with new message ID: {last_message_id}")
                    state_manager.save_state(last_message_id, previous_present_members)
        
            logger.info("Single run completed successfully")
            
            execution_time = time.time() - start_time
            sleep_time = max(0, POLLING_INTERVAL - execution_time)
            
            logger.info(f"Run took {execution_time:.2f} seconds")
            logger.info(f"Waiting {sleep_time:.2f} seconds until next run")
            await asyncio.sleep(sleep_time)
        
        except Exception as e:
            logger.error(f"Error in main execution: {e}", exc_info=True)
            if retries < MAX_RETRIES:
                retries += 1
                await asyncio.sleep(POLLING_INTERVAL)
            else:
                logger.error("Max retries reached")
                await asyncio.sleep(POLLING_INTERVAL)

if __name__ == "__main__":
    asyncio.run(main())