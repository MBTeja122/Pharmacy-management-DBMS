from .nlp import parse_input
from .logic import execute_logic
from .storage import log_interaction, setup_cache
import time

def get_bot_response(user_id, message):
    start_time = time.time()
    try:
        if not message or not message.strip():
            return "❓ Please type a message to get started."
        
        # 1. PARSE (Simple returns: intent, entity)
        intent, entity = parse_input(message)
        
        # 2. EXECUTE (Simple logic)
        response = execute_logic(intent, entity, user_id, message)
        
        # 3. LOG
        exec_time = int((time.time() - start_time) * 1000)
        confidence = entity.get('confidence', 0.0) if entity else 0.0
        log_interaction(user_id, message, response, intent, confidence, exec_time)
        
        return response
    except Exception as e:
        print(f"❌ Chatbot Error: {e}")
        return "🤖 I'm experiencing technical difficulties."

__all__ = ['get_bot_response', 'setup_cache']