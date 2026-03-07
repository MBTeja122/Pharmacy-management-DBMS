from flask import Blueprint, request, jsonify, session
import time
import sys
import os

# Add parent directory to path to import chatbot module
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from chatbot import get_bot_response, setup_cache
except ImportError:
    from .chatbot import get_bot_response, setup_cache

# Create Blueprint
chatbot_bp = Blueprint('chatbot_bp', __name__)

@chatbot_bp.route('/admin/chat_api', methods=['POST'])
def chat_api():
    """
    Main chatbot endpoint for handling user messages.
    Expected JSON: {"message": "user message here"}
    Returns JSON: {"reply": "bot response", "status": "success", ...}
    """
    start_time = time.time()
    
    try:
        # Parse request data
        data = request.get_json()
        
        if not data:
            return jsonify({
                "reply": "❌ Invalid request format. Please send JSON data.",
                "status": "error"
            }), 400
        
        user_msg = data.get('message', '').strip()
        
        # Validate message
        if not user_msg:
            return jsonify({
                "reply": "❓ Please type a message.",
                "status": "error"
            }), 400
        
        # Get user identifier from session
        user_id = session.get('username') or session.get('user_id') or session.get('pharmacist_id') or 'guest_user'
        
        # Get AI Response (FIX: Correct parameter order)
        reply = get_bot_response(user_id, user_msg)
        
        # Calculate execution time
        exec_time = int((time.time() - start_time) * 1000)
        
        # Return successful response
        return jsonify({
            "reply": reply,
            "status": "success",
            "execution_time_ms": exec_time,
            "user_id": user_id
        }), 200
    
    except Exception as e:
        print(f"❌ Chatbot Route Error: {e}")
        import traceback
        traceback.print_exc()
        
        return jsonify({
            "reply": "🤖 My systems are experiencing issues. Please try again in a moment.",
            "error": str(e),
            "status": "error"
        }), 500

@chatbot_bp.route('/admin/chat_refresh_cache', methods=['POST'])
def refresh_cache():
    """
    Endpoint to manually refresh the medicine/supplier/customer cache.
    This improves fuzzy matching performance.
    """
    try:
        setup_cache()
        return jsonify({
            "message": "✅ Cache refreshed successfully. Entity matching updated.",
            "status": "success"
        }), 200
    except Exception as e:
        print(f"❌ Cache Refresh Error: {e}")
        return jsonify({
            "message": f"❌ Error refreshing cache: {str(e)}",
            "status": "error"
        }), 500

@chatbot_bp.route('/admin/chat_health', methods=['GET'])
def health_check():
    """
    Health check endpoint to verify chatbot service is running.
    """
    try:
        return jsonify({
            "status": "healthy",
            "service": "pharmacy_chatbot",
            "timestamp": time.time()
        }), 200
    except Exception as e:
        return jsonify({
            "status": "unhealthy",
            "error": str(e)
        }), 500

# Optional: Chat history endpoint
@chatbot_bp.route('/admin/chat_history', methods=['GET'])
def chat_history():
    """
    Retrieve chat history for current user.
    """
    try:
        user_id = session.get('username') or session.get('user_id') or 'guest_user'
        
        # Import here to avoid circular imports
        from storage import get_db_connection
        
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT user_message, bot_response, detected_intent, created_at
            FROM bot_logs
            WHERE user_identifier = %s
            ORDER BY created_at DESC
            LIMIT 50
        """, (user_id,))
        
        rows = cur.fetchall()
        cur.close()
        conn.close()
        
        history = [{
            'user_message': r['user_message'],
            'bot_response': r['bot_response'],
            'intent': r['detected_intent'],
            'timestamp': r['created_at'].isoformat() if r['created_at'] else None
        } for r in rows]
        
        return jsonify({
            "history": history,
            "status": "success",
            "count": len(history)
        }), 200
        
    except Exception as e:
        print(f"❌ History Error: {e}")
        return jsonify({
            "message": f"Error retrieving history: {str(e)}",
            "status": "error"
        }), 500