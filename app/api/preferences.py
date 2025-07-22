from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

from app.database.database import get_db


router = APIRouter()


class PreferenceUpdate(BaseModel):
    preference_type: str
    preference_value: str
    confidence_score: Optional[float] = 1.0
    is_explicit: Optional[bool] = True


class UserPreferences(BaseModel):
    session_id: str
    preferences: Dict[str, Any]
    summary: str


@router.get("/{session_id}", response_model=UserPreferences)
async def get_user_preferences(
    session_id: str,
    db: Session = Depends(get_db)
):
    """
    Get all learned preferences for a user session.
    """
    try:
        from app.database.models import User, UserPreference
        from app.agents.preference_learner import PreferenceLearner
        
        # Get user
        user = db.query(User).filter(User.session_id == session_id).first()
        if not user:
            return UserPreferences(
                session_id=session_id,
                preferences={},
                summary="No preferences learned yet."
            )
        
        # Get preferences
        preferences = (
            db.query(UserPreference)
            .filter(UserPreference.user_id == user.id)
            .all()
        )
        
        # Format preferences
        prefs_dict = {}
        for pref in preferences:
            prefs_dict[pref.preference_type] = {
                "value": pref.preference_value,
                "confidence_score": pref.confidence_score,
                "is_explicit": pref.is_explicit,
                "created_at": pref.created_at.isoformat(),
                "updated_at": pref.updated_at.isoformat() if pref.updated_at else None
            }
        
        # Generate summary
        preference_learner = PreferenceLearner(db)
        summary = preference_learner.get_user_preferences_summary(user.id)
        
        return UserPreferences(
            session_id=session_id,
            preferences=prefs_dict,
            summary=summary
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving preferences: {str(e)}"
        )


@router.post("/{session_id}/update")
async def update_user_preference(
    session_id: str,
    preference_update: PreferenceUpdate,
    db: Session = Depends(get_db)
):
    """
    Manually update a user preference.
    """
    try:
        from app.database.models import User, UserPreference
        
        # Get or create user
        user = db.query(User).filter(User.session_id == session_id).first()
        if not user:
            user = User(session_id=session_id)
            db.add(user)
            db.commit()
            db.refresh(user)
        
        # Check if preference exists
        existing_pref = (
            db.query(UserPreference)
            .filter(
                UserPreference.user_id == user.id,
                UserPreference.preference_type == preference_update.preference_type
            )
            .first()
        )
        
        if existing_pref:
            # Update existing preference
            existing_pref.preference_value = preference_update.preference_value
            existing_pref.confidence_score = preference_update.confidence_score
            existing_pref.is_explicit = preference_update.is_explicit
        else:
            # Create new preference
            new_pref = UserPreference(
                user_id=user.id,
                preference_type=preference_update.preference_type,
                preference_value=preference_update.preference_value,
                confidence_score=preference_update.confidence_score,
                is_explicit=preference_update.is_explicit
            )
            db.add(new_pref)
        
        db.commit()
        
        return {
            "status": "success",
            "message": f"Preference '{preference_update.preference_type}' updated successfully",
            "preference": {
                "type": preference_update.preference_type,
                "value": preference_update.preference_value,
                "confidence_score": preference_update.confidence_score,
                "is_explicit": preference_update.is_explicit
            }
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error updating preference: {str(e)}"
        )


@router.delete("/{session_id}/{preference_type}")
async def delete_user_preference(
    session_id: str,
    preference_type: str,
    db: Session = Depends(get_db)
):
    """
    Delete a specific user preference.
    """
    try:
        from app.database.models import User, UserPreference
        
        # Get user
        user = db.query(User).filter(User.session_id == session_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User session not found")
        
        # Find and delete preference
        preference = (
            db.query(UserPreference)
            .filter(
                UserPreference.user_id == user.id,
                UserPreference.preference_type == preference_type
            )
            .first()
        )
        
        if not preference:
            raise HTTPException(status_code=404, detail="Preference not found")
        
        db.delete(preference)
        db.commit()
        
        return {
            "status": "success",
            "message": f"Preference '{preference_type}' deleted successfully"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error deleting preference: {str(e)}"
        )


@router.delete("/{session_id}")
async def clear_all_preferences(
    session_id: str,
    db: Session = Depends(get_db)
):
    """
    Clear all preferences for a user session.
    """
    try:
        from app.database.models import User, UserPreference
        
        # Get user
        user = db.query(User).filter(User.session_id == session_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User session not found")
        
        # Delete all preferences
        deleted_count = (
            db.query(UserPreference)
            .filter(UserPreference.user_id == user.id)
            .delete()
        )
        
        db.commit()
        
        return {
            "status": "success",
            "message": f"Cleared {deleted_count} preferences successfully"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error clearing preferences: {str(e)}"
        )


@router.post("/{session_id}/analyze")
async def analyze_preferences_from_text(
    session_id: str,
    text_data: Dict[str, str],
    db: Session = Depends(get_db)
):
    """
    Analyze text and extract preferences using AI.
    """
    try:
        from app.database.models import User
        from app.agents.preference_learner import PreferenceLearner
        
        text = text_data.get("text", "")
        if not text:
            raise HTTPException(status_code=400, detail="Text is required")
        
        # Get or create user
        user = db.query(User).filter(User.session_id == session_id).first()
        if not user:
            user = User(session_id=session_id)
            db.add(user)
            db.commit()
            db.refresh(user)
        
        # Extract preferences
        preference_learner = PreferenceLearner(db)
        extracted_preferences = await preference_learner.extract_preferences(text, user.id)
        
        return {
            "status": "success",
            "message": f"Extracted {len(extracted_preferences)} preferences",
            "extracted_preferences": extracted_preferences
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error analyzing preferences: {str(e)}"
        )


@router.get("/{session_id}/insights")
async def get_preference_insights(
    session_id: str,
    db: Session = Depends(get_db)
):
    """
    Get insights and analytics about user preferences.
    """
    try:
        from app.database.models import User, UserPreference
        
        # Get user
        user = db.query(User).filter(User.session_id == session_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User session not found")
        
        # Get all preferences
        preferences = (
            db.query(UserPreference)
            .filter(UserPreference.user_id == user.id)
            .all()
        )
        
        if not preferences:
            return {
                "session_id": session_id,
                "total_preferences": 0,
                "insights": "No preferences to analyze yet."
            }
        
        # Calculate insights
        explicit_count = sum(1 for p in preferences if p.is_explicit)
        implicit_count = len(preferences) - explicit_count
        
        high_confidence = sum(1 for p in preferences if p.confidence_score >= 0.8)
        medium_confidence = sum(1 for p in preferences if 0.5 <= p.confidence_score < 0.8)
        low_confidence = sum(1 for p in preferences if p.confidence_score < 0.5)
        
        avg_confidence = sum(p.confidence_score for p in preferences) / len(preferences)
        
        # Categorize preferences
        categories = {}
        for pref in preferences:
            category = _categorize_preference(pref.preference_type)
            if category not in categories:
                categories[category] = 0
            categories[category] += 1
        
        return {
            "session_id": session_id,
            "total_preferences": len(preferences),
            "explicit_preferences": explicit_count,
            "implicit_preferences": implicit_count,
            "confidence_distribution": {
                "high": high_confidence,
                "medium": medium_confidence,
                "low": low_confidence
            },
            "average_confidence": round(avg_confidence, 2),
            "preference_categories": categories,
            "insights": _generate_insights(preferences, avg_confidence, explicit_count, len(preferences))
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating insights: {str(e)}"
        )


def _categorize_preference(preference_type: str) -> str:
    """Categorize preference types"""
    location_types = ['location', 'postcode', 'area']
    financial_types = ['max_price', 'min_price', 'budget']
    property_types = ['property_type', 'min_bedrooms', 'max_bedrooms', 'bathrooms']
    feature_types = ['garden', 'parking', 'balcony', 'specific_features']
    lifestyle_types = ['lifestyle', 'transport_links', 'schools', 'quiet', 'vibrant']
    
    if preference_type in location_types:
        return "Location"
    elif preference_type in financial_types:
        return "Financial"
    elif preference_type in property_types:
        return "Property Specs"
    elif preference_type in feature_types:
        return "Features"
    elif preference_type in lifestyle_types:
        return "Lifestyle"
    else:
        return "Other"


def _generate_insights(preferences, avg_confidence, explicit_count, total_count) -> str:
    """Generate textual insights about preferences"""
    insights = []
    
    if avg_confidence >= 0.8:
        insights.append("You have very clear and well-defined preferences.")
    elif avg_confidence >= 0.6:
        insights.append("Your preferences are fairly well established.")
    else:
        insights.append("Your preferences are still being learned and refined.")
    
    explicit_ratio = explicit_count / total_count if total_count > 0 else 0
    if explicit_ratio >= 0.7:
        insights.append("Most of your preferences have been explicitly stated.")
    elif explicit_ratio >= 0.4:
        insights.append("You have a good mix of explicit and inferred preferences.")
    else:
        insights.append("Many of your preferences have been inferred from conversation.")
    
    if total_count >= 10:
        insights.append("REAgent has learned a comprehensive set of preferences about your ideal home.")
    elif total_count >= 5:
        insights.append("A good foundation of preferences has been established.")
    else:
        insights.append("Continue chatting to help REAgent learn more about your preferences.")
    
    return " ".join(insights) 