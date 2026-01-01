from flask import Blueprint, request, jsonify, session
from chatbot import get_bot_response
# Ensure you import other necessary modules like logging if needed

chatbot_bp = Blueprint('chatbot_bp', __name__)

@chatbot_bp.route('/admin/chat_api', methods=['POST'])
def chat_api():
    try:
        data = request.json
        user_msg = data.get('message', '')
        
        # 1. IDENTIFY USER
        # Use session username as the unique ID for DB memory
        # If user is not logged in, default to 'guest'
        user_id = session.get('username', session.get('user_id', 'guest_user'))
        
        # 2. CALL THE BRAIN
        # We pass the user_id so the bot loads the correct memory from Postgres
        reply = get_bot_response(user_msg, user_id)
        
        # 3. OPTIONAL: LOGGING
        # You could insert into 'bot_logs' table here if you created it
        
        return jsonify({"reply": reply, "status": "success"})

    except Exception as e:
        print(f"Chatbot Route Error: {e}")
        return jsonify({"reply": "My brain is offline (Server Error).", "error": str(e)}), 500