from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from db import db
from models import ChatbotConversation, ChatbotMessage, ChatbotFeedback
from services.rag_service import generate_rag_answer, detect_language

chat_bp = Blueprint('chat', __name__)

@chat_bp.route('/conversations', methods=['GET'])
@jwt_required()
def get_conversations():
    """List authenticated user's chatbot conversations."""
    user_id = int(get_jwt_identity())
    convs = ChatbotConversation.query.filter_by(user_id=user_id).order_by(
        ChatbotConversation.updated_at.desc()
    ).all()

    return jsonify({
        'success': True,
        'conversations': [c.to_dict() for c in convs]
    }), 200

@chat_bp.route('/conversations', methods=['POST'])
@jwt_required()
def create_conversation():
    """Start a new chat session."""
    user_id = int(get_jwt_identity())
    data = request.get_json() or {}
    title = data.get('session_title', 'Academic Inquiries').strip()
    language = data.get('language', 'en')

    conv = ChatbotConversation(
        user_id=user_id,
        session_title=title,
        language=language
    )
    db.session.add(conv)
    db.session.commit()

    return jsonify({
        'success': True,
        'conversation': conv.to_dict()
    }), 201

@chat_bp.route('/conversations/<int:conv_id>/messages', methods=['GET'])
@jwt_required()
def get_conversation_messages(conv_id):
    """Retrieve message history for a conversation (user ownership enforced)."""
    user_id = int(get_jwt_identity())
    conv = ChatbotConversation.query.filter_by(id=conv_id, user_id=user_id).first()
    if not conv:
        return jsonify({'success': False, 'message': 'Conversation not found or access denied.'}), 404

    messages = ChatbotMessage.query.filter_by(conversation_id=conv_id).order_by(
        ChatbotMessage.created_at.asc()
    ).all()

    return jsonify({
        'success': True,
        'conversation': conv.to_dict(),
        'messages': [m.to_dict() for m in messages]
    }), 200

@chat_bp.route('/message', methods=['POST'])
@jwt_required()
def send_chat_message():
    """
    Main Multilingual Academic Chatbot Endpoint:
    - Supports English, Tamil (தமிழ்), and Tanglish
    - Retrieves verified chunks from active academic PDFs
    - Shows source document names and page numbers
    - Adheres to academic integrity: never invents facts when unsupported
    - Provides official department contacts when unavailable
    - Provides usable document-retrieval fallback when no AI API key is set
    - Persists query and response securely in MySQL
    """
    user_id = int(get_jwt_identity())
    data = request.get_json() or {}
    query = data.get('message', '').strip()
    conv_id = data.get('conversation_id')

    if not query:
        return jsonify({'success': False, 'message': 'Message text cannot be empty.'}), 400

    # Ensure valid conversation
    if conv_id:
        conv = ChatbotConversation.query.filter_by(id=conv_id, user_id=user_id).first()
    else:
        conv = None

    if not conv:
        detected_lang = detect_language(query)
        conv = ChatbotConversation(
            user_id=user_id,
            session_title=query[:40] + ('...' if len(query) > 40 else ''),
            language=detected_lang
        )
        db.session.add(conv)
        db.session.flush()

    detected_lang = detect_language(query)

    # 1. Save user message
    user_msg = ChatbotMessage(
        conversation_id=conv.id,
        sender='user',
        message=query,
        detected_language=detected_lang,
        is_fallback=False,
        is_supported_by_docs=True
    )
    db.session.add(user_msg)
    db.session.flush()

    # 2. Run Multilingual RAG
    rag_result = generate_rag_answer(query, user_id=user_id)

    # 3. Save assistant response with source citations
    assistant_msg = ChatbotMessage(
        conversation_id=conv.id,
        sender='assistant',
        message=rag_result['answer'],
        detected_language=rag_result['detected_language'],
        retrieved_sources=rag_result['sources'],
        is_fallback=rag_result['is_fallback'],
        is_supported_by_docs=rag_result['is_supported_by_docs']
    )
    db.session.add(assistant_msg)
    db.session.commit()

    return jsonify({
        'success': True,
        'conversation_id': conv.id,
        'user_message': user_msg.to_dict(),
        'assistant_message': assistant_msg.to_dict()
    }), 200

@chat_bp.route('/feedback', methods=['POST'])
@jwt_required()
def submit_feedback():
    """Record student feedback (thumbs up / helpful vs unhelpful) for chatbot quality monitoring."""
    user_id = int(get_jwt_identity())
    data = request.get_json() or {}

    message_id = data.get('message_id')
    rating = data.get('rating', 'helpful').lower() # helpful or unhelpful
    comments = data.get('comments', '')

    if not message_id or rating not in ['helpful', 'unhelpful']:
        return jsonify({'success': False, 'message': 'Valid message_id and rating (helpful/unhelpful) are required.'}), 400

    feedback = ChatbotFeedback(
        message_id=message_id,
        user_id=user_id,
        rating=rating,
        comments=comments
    )
    db.session.add(feedback)
    db.session.commit()

    return jsonify({
        'success': True,
        'message': 'Thank you! Your feedback has been recorded.',
        'feedback': feedback.to_dict()
    }), 201

@chat_bp.route('/conversations/<int:conv_id>', methods=['DELETE'])
@jwt_required()
def delete_conversation(conv_id):
    """Delete conversation and all its messages."""
    user_id = int(get_jwt_identity())
    conv = ChatbotConversation.query.filter_by(id=conv_id, user_id=user_id).first()
    if not conv:
        return jsonify({'success': False, 'message': 'Conversation not found or access denied.'}), 404

    db.session.delete(conv)
    db.session.commit()

    return jsonify({'success': True, 'message': 'Conversation deleted successfully.'}), 200
