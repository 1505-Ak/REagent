from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

from app.database.database import get_db
from app.integrations.property_platforms import PropertyPlatformManager


router = APIRouter()


class PropertySearchCriteria(BaseModel):
    location: Optional[str] = None
    max_price: Optional[int] = None
    min_price: Optional[int] = None
    min_bedrooms: Optional[int] = None
    max_bedrooms: Optional[int] = None
    property_type: Optional[str] = None
    features: Optional[List[str]] = None


class PropertyResponse(BaseModel):
    properties: List[Dict[str, Any]]
    total_count: int
    search_criteria: Dict[str, Any]


@router.post("/search", response_model=PropertyResponse)
async def search_properties(
    criteria: PropertySearchCriteria,
    db: Session = Depends(get_db)
):
    """
    Search for properties across multiple platforms based on criteria.
    """
    try:
        # Convert criteria to dict
        search_criteria = {
            k: v for k, v in criteria.dict().items() 
            if v is not None
        }
        
        # Initialize property platform manager
        property_manager = PropertyPlatformManager()
        
        # Search properties
        properties = await property_manager.search_properties(search_criteria)
        
        return PropertyResponse(
            properties=properties,
            total_count=len(properties),
            search_criteria=search_criteria
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error searching properties: {str(e)}"
        )


@router.get("/", response_model=PropertyResponse)
async def get_properties(
    location: Optional[str] = Query(None, description="Location to search"),
    max_price: Optional[int] = Query(None, description="Maximum price"),
    min_price: Optional[int] = Query(None, description="Minimum price"),
    min_bedrooms: Optional[int] = Query(None, description="Minimum bedrooms"),
    max_bedrooms: Optional[int] = Query(None, description="Maximum bedrooms"),
    property_type: Optional[str] = Query(None, description="Property type"),
    db: Session = Depends(get_db)
):
    """
    Get properties using query parameters.
    """
    criteria = PropertySearchCriteria(
        location=location,
        max_price=max_price,
        min_price=min_price,
        min_bedrooms=min_bedrooms,
        max_bedrooms=max_bedrooms,
        property_type=property_type
    )
    
    return await search_properties(criteria, db)


@router.get("/{property_id}")
async def get_property_details(
    property_id: str,
    platform: str = Query(..., description="Platform: zoopla or rightmove"),
    db: Session = Depends(get_db)
):
    """
    Get detailed information about a specific property.
    """
    try:
        from app.database.models import Property
        
        # First check if property exists in our database
        property_obj = (
            db.query(Property)
            .filter(
                Property.external_id == property_id,
                Property.platform == platform
            )
            .first()
        )
        
        if property_obj:
            return {
                "id": property_obj.id,
                "external_id": property_obj.external_id,
                "platform": property_obj.platform,
                "title": property_obj.title,
                "description": property_obj.description,
                "price": property_obj.price,
                "bedrooms": property_obj.bedrooms,
                "bathrooms": property_obj.bathrooms,
                "property_type": property_obj.property_type,
                "location": property_obj.location,
                "postcode": property_obj.postcode,
                "latitude": property_obj.latitude,
                "longitude": property_obj.longitude,
                "images": property_obj.images,
                "features": property_obj.features,
                "agent_info": property_obj.agent_info,
                "url": property_obj.url,
                "created_at": property_obj.created_at.isoformat()
            }
        
        # If not in database, could fetch from platform APIs
        # For now, return not found
        raise HTTPException(
            status_code=404,
            detail="Property not found"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving property details: {str(e)}"
        )


@router.get("/recommendations/{session_id}")
async def get_property_recommendations(
    session_id: str,
    limit: int = Query(10, description="Number of recommendations to return"),
    db: Session = Depends(get_db)
):
    """
    Get personalized property recommendations for a user session.
    """
    try:
        from app.database.models import User, PropertyRecommendation, Property
        from app.agents.core_agent import REAgent
        
        # Get user
        user = db.query(User).filter(User.session_id == session_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User session not found")
        
        # Get existing recommendations
        recommendations = (
            db.query(PropertyRecommendation)
            .join(Property)
            .filter(PropertyRecommendation.user_id == user.id)
            .order_by(PropertyRecommendation.relevance_score.desc())
            .limit(limit)
            .all()
        )
        
        result = []
        for rec in recommendations:
            result.append({
                "recommendation_id": rec.id,
                "relevance_score": rec.relevance_score,
                "reasoning": rec.reasoning,
                "pros": rec.pros,
                "cons": rec.cons,
                "viewed": rec.viewed,
                "user_feedback": rec.user_feedback,
                "property": {
                    "id": rec.property.id,
                    "external_id": rec.property.external_id,
                    "platform": rec.property.platform,
                    "title": rec.property.title,
                    "description": rec.property.description,
                    "price": rec.property.price,
                    "bedrooms": rec.property.bedrooms,
                    "bathrooms": rec.property.bathrooms,
                    "property_type": rec.property.property_type,
                    "location": rec.property.location,
                    "images": rec.property.images,
                    "features": rec.property.features,
                    "url": rec.property.url
                }
            })
        
        return {
            "recommendations": result,
            "total_count": len(result),
            "session_id": session_id
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving recommendations: {str(e)}"
        )


@router.post("/save")
async def save_property(
    request_data: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """
    Save a property to the database for future reference.
    """
    try:
        from app.database.models import Property
        
        # Check if property already exists
        existing_property = (
            db.query(Property)
            .filter(
                Property.external_id == request_data.get("external_id"),
                Property.platform == request_data.get("platform")
            )
            .first()
        )
        
        if existing_property:
            return {
                "status": "exists",
                "property_id": existing_property.id,
                "message": "Property already saved"
            }
        
        # Create new property
        property_obj = Property(**request_data)
        db.add(property_obj)
        db.commit()
        db.refresh(property_obj)
        
        return {
            "status": "saved",
            "property_id": property_obj.id,
            "message": "Property saved successfully"
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error saving property: {str(e)}"
        ) 