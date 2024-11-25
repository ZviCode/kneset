import json
from config import STORAGE_FILE
from utils.logger import logger

class StateManager:
    @staticmethod
    def load_state():
        try:
            if STORAGE_FILE.exists():
                with open(STORAGE_FILE, 'r') as f:
                    state = json.load(f)
                    return state.get('last_message_id'), set(state.get('previous_present_members', []))
        except Exception as e:
            logger.error(f"Error loading state: {e}")
        return None, set()

    @staticmethod
    def save_state(last_message_id, previous_present_members):
        try:
            state = {
                'last_message_id': last_message_id,
                'previous_present_members': list(previous_present_members)
            }
            with open(STORAGE_FILE, 'w') as f:
                json.dump(state, f)
            return True
        except Exception as e:
            logger.error(f"Error saving state: {e}")
            return False