from sqlalchemy import Column, Integer, String, Text, DateTime, Float, Boolean, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.database import Base


class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, unique=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    conversations = relationship("Conversation", back_populates="user")
    preferences = relationship("UserPreference", back_populates="user")


class Conversation(Base):
    __tablename__ = "conversations"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    message = Column(Text, nullable=False)
    response = Column(Text, nullable=False)
    message_type = Column(String)  # 'user', 'agent', 'system'
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="conversations")


class UserPreference(Base):
    __tablename__ = "user_preferences"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    preference_type = Column(String, nullable=False)  # 'location', 'price', 'bedrooms', etc.
    preference_value = Column(String, nullable=False)
    confidence_score = Column(Float, default=1.0)
    is_explicit = Column(Boolean, default=True)  # True if explicitly stated, False if inferred
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="preferences")


class Property(Base):
    __tablename__ = "properties"
    
    id = Column(Integer, primary_key=True, index=True)
    external_id = Column(String, unique=True, index=True)  # ID from Zoopla/Rightmove
    platform = Column(String, nullable=False)  # 'zoopla', 'rightmove'
    title = Column(String, nullable=False)
    description = Column(Text)
    price = Column(Integer)
    bedrooms = Column(Integer)
    bathrooms = Column(Integer)
    property_type = Column(String)  # 'house', 'flat', 'studio', etc.
    location = Column(String, nullable=False)
    postcode = Column(String)
    latitude = Column(Float)
    longitude = Column(Float)
    images = Column(JSON)  # Array of image URLs
    features = Column(JSON)  # Array of property features
    agent_info = Column(JSON)  # Estate agent contact details
    url = Column(String)  # Link to original listing
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    recommendations = relationship("PropertyRecommendation", back_populates="property")


class PropertyRecommendation(Base):
    __tablename__ = "property_recommendations"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    property_id = Column(Integer, ForeignKey("properties.id"))
    relevance_score = Column(Float, nullable=False)
    reasoning = Column(Text)  # AI explanation for why this property was recommended
    pros = Column(JSON)  # Array of pros based on user preferences
    cons = Column(JSON)  # Array of cons based on user preferences
    viewed = Column(Boolean, default=False)
    user_feedback = Column(String)  # 'interested', 'not_interested', 'viewed'
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    property = relationship("Property", back_populates="recommendations") 