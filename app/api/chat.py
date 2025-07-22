from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import uuid

from app.database.database import get_db
from app.agents.core_agent import REAgent


router = APIRouter()


class ChatMessage(BaseModel):
    message: str
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    response: str
    recommendations: List[Dict[str, Any]]
    extracted_preferences: List[Dict[str, Any]]
    conversation_id: int
    session_id: str


class ConversationHistory(BaseModel):
    conversations: List[Dict[str, Any]]
    user_preferences: Dict[str, Any]


@router.post("/message", response_model=ChatResponse)
async def send_message(
    chat_message: ChatMessage,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Send a message to REAgent and get an intelligent response with property recommendations.
    """
    try:
        # Generate session ID if not provided
        session_id = chat_message.session_id or str(uuid.uuid4())
        
        # Initialize REAgent
        agent = REAgent(db)
        
        # Process the message
        result = await agent.process_message(
            user_id=0,  # Will be determined by agent based on session_id
            message=chat_message.message,
            session_id=session_id
        )
        
        return ChatResponse(
            response=result["response"],
            recommendations=result["recommendations"],
            extracted_preferences=result["extracted_preferences"],
            conversation_id=result["conversation_id"],
            session_id=session_id
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing message: {str(e)}"
        )


@router.get("/history/{session_id}", response_model=ConversationHistory)
async def get_conversation_history(
    session_id: str,
    db: Session = Depends(get_db)
):
    """
    Get conversation history and learned preferences for a session.
    """
    try:
        from app.database.models import User, Conversation, UserPreference
        
        # Get user by session ID
        user = db.query(User).filter(User.session_id == session_id).first()
        
        if not user:
            return ConversationHistory(
                conversations=[],
                user_preferences={}
            )
        
        # Get conversation history
        conversations = (
            db.query(Conversation)
            .filter(Conversation.user_id == user.id)
            .order_by(Conversation.created_at.desc())
            .limit(50)
            .all()
        )
        
        # Format conversations
        conversation_list = []
        for conv in reversed(conversations):
            conversation_list.append({
                "id": conv.id,
                "message": conv.message,
                "response": conv.response,
                "message_type": conv.message_type,
                "created_at": conv.created_at.isoformat()
            })
        
        # Get user preferences
        preferences = (
            db.query(UserPreference)
            .filter(UserPreference.user_id == user.id)
            .all()
        )
        
        user_prefs = {}
        for pref in preferences:
            user_prefs[pref.preference_type] = {
                "value": pref.preference_value,
                "confidence": pref.confidence_score,
                "is_explicit": pref.is_explicit,
                "updated_at": pref.updated_at.isoformat() if pref.updated_at else None
            }
        
        return ConversationHistory(
            conversations=conversation_list,
            user_preferences=user_prefs
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving conversation history: {str(e)}"
        )


@router.post("/feedback")
async def provide_feedback(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Provide feedback on property recommendations to improve future suggestions.
    """
    try:
        data = await request.json()
        
        session_id = data.get("session_id")
        property_id = data.get("property_id")
        feedback = data.get("feedback")  # 'interested', 'not_interested', 'viewed'
        
        if not all([session_id, property_id, feedback]):
            raise HTTPException(
                status_code=400,
                detail="session_id, property_id, and feedback are required"
            )
        
        from app.database.models import User, PropertyRecommendation
        
        # Get user
        user = db.query(User).filter(User.session_id == session_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User session not found")
        
        # Update recommendation feedback
        recommendation = (
            db.query(PropertyRecommendation)
            .filter(
                PropertyRecommendation.user_id == user.id,
                PropertyRecommendation.property_id == property_id
            )
            .first()
        )
        
        if recommendation:
            recommendation.user_feedback = feedback
            db.commit()
        
        # TODO: Use feedback to update preference learning model
        
        return {"status": "success", "message": "Feedback recorded"}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing feedback: {str(e)}"
        )


@router.delete("/session/{session_id}")
async def clear_session(
    session_id: str,
    db: Session = Depends(get_db)
):
    """
    Clear conversation history and preferences for a session.
    """
    try:
        from app.database.models import User, Conversation, UserPreference
        
        # Get user
        user = db.query(User).filter(User.session_id == session_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User session not found")
        
        # Delete conversations
        db.query(Conversation).filter(Conversation.user_id == user.id).delete()
        
        # Delete preferences
        db.query(UserPreference).filter(UserPreference.user_id == user.id).delete()
        
        # Delete user
        db.delete(user)
        
        db.commit()
        
        return {"status": "success", "message": "Session cleared"}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error clearing session: {str(e)}"
        ) 