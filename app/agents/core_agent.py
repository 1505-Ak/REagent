from typing import List, Dict, Any, Optional
import json
from datetime import datetime
from sqlalchemy.orm import Session
from openai import OpenAI

from app.core.config import get_settings
from app.database.models import User, Conversation, UserPreference, PropertyRecommendation
from app.agents.preference_learner import PreferenceLearner
from app.integrations.property_platforms import PropertyPlatformManager


class REAgent:
    """
    The core REAgent - an autonomous AI real estate concierge that learns preferences
    and provides personalized property recommendations through natural conversation.
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.settings = get_settings()
        self.openai_client = OpenAI(api_key=self.settings.openai_api_key)
        self.preference_learner = PreferenceLearner(db)
        self.property_manager = PropertyPlatformManager()
        
        # Agent personality and system prompt
        self.system_prompt = """
        You are REAgent, an intelligent and friendly AI real estate concierge. Your mission is to help users find their perfect home through natural conversation.

        Core capabilities:
        - Learn user preferences dynamically from conversation
        - Search and analyze real-time property listings
        - Provide personalized recommendations with pros/cons
        - Handle logistics like viewing arrangements
        - Adapt and improve with each interaction

        Personality:
        - Warm, helpful, and professional
        - Proactive in asking clarifying questions
        - Enthusiastic about helping find the perfect home
        - Expert knowledge of UK property market
        - Patient and understanding of changing needs

        Always:
        - Ask follow-up questions to understand preferences better
        - Explain your reasoning for recommendations
        - Highlight both pros and cons of properties
        - Offer to help with next steps (viewings, agent contact)
        - Remember and reference previous conversation context
        """

    async def process_message(self, user_id: int, message: str, session_id: str) -> Dict[str, Any]:
        """
        Process a user message and generate an intelligent response with recommendations.
        """
        try:
            # Get or create user
            user = self._get_or_create_user(session_id)
            
            # Store user message
            self._store_conversation(user.id, message, "", "user")
            
            # Get conversation history
            conversation_history = self._get_conversation_history(user.id)
            
            # Extract and update preferences from the message
            extracted_prefs = await self.preference_learner.extract_preferences(message, user.id)
            
            # Get current user preferences
            current_preferences = self._get_user_preferences(user.id)
            
            # Search for properties based on preferences
            properties = await self._search_properties(current_preferences)
            
            # Generate AI response
            ai_response = await self._generate_response(
                message, conversation_history, current_preferences, properties
            )
            
            # Store AI response
            self._store_conversation(user.id, message, ai_response["content"], "agent")
            
            # Generate property recommendations if any found
            recommendations = []
            if properties:
                recommendations = await self._generate_recommendations(user.id, properties, current_preferences)
            
            return {
                "response": ai_response["content"],
                "recommendations": recommendations,
                "extracted_preferences": extracted_prefs,
                "conversation_id": user.id
            }
            
        except Exception as e:
            error_response = "I apologize, but I encountered an issue processing your request. Could you please try again?"
            return {
                "response": error_response,
                "recommendations": [],
                "extracted_preferences": [],
                "error": str(e)
            }

    def _get_or_create_user(self, session_id: str) -> User:
        """Get existing user or create new one based on session ID"""
        user = self.db.query(User).filter(User.session_id == session_id).first()
        if not user:
            user = User(session_id=session_id)
            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)
        return user

    def _store_conversation(self, user_id: int, message: str, response: str, message_type: str):
        """Store conversation in database"""
        conversation = Conversation(
            user_id=user_id,
            message=message,
            response=response,
            message_type=message_type
        )
        self.db.add(conversation)
        self.db.commit()

    def _get_conversation_history(self, user_id: int) -> List[Dict[str, str]]:
        """Get recent conversation history for context"""
        conversations = (
            self.db.query(Conversation)
            .filter(Conversation.user_id == user_id)
            .order_by(Conversation.created_at.desc())
            .limit(self.settings.max_conversation_history)
            .all()
        )
        
        history = []
        for conv in reversed(conversations):
            if conv.message_type == "user":
                history.append({"role": "user", "content": conv.message})
            elif conv.message_type == "agent":
                history.append({"role": "assistant", "content": conv.response})
        
        return history

    def _get_user_preferences(self, user_id: int) -> Dict[str, Any]:
        """Get current user preferences"""
        preferences = (
            self.db.query(UserPreference)
            .filter(UserPreference.user_id == user_id)
            .all()
        )
        
        prefs_dict = {}
        for pref in preferences:
            prefs_dict[pref.preference_type] = {
                "value": pref.preference_value,
                "confidence": pref.confidence_score,
                "is_explicit": pref.is_explicit
            }
        
        return prefs_dict

    async def _search_properties(self, preferences: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Search for properties based on user preferences"""
        try:
            # Extract search criteria from preferences
            search_criteria = {}
            
            if "location" in preferences:
                search_criteria["location"] = preferences["location"]["value"]
            if "max_price" in preferences:
                search_criteria["max_price"] = preferences["max_price"]["value"]
            if "min_bedrooms" in preferences:
                search_criteria["min_bedrooms"] = preferences["min_bedrooms"]["value"]
            if "property_type" in preferences:
                search_criteria["property_type"] = preferences["property_type"]["value"]
            
            # Search across platforms
            properties = await self.property_manager.search_properties(search_criteria)
            return properties[:10]  # Limit to top 10 results
            
        except Exception as e:
            print(f"Error searching properties: {e}")
            return []

    async def _generate_response(
        self, 
        message: str, 
        history: List[Dict[str, str]], 
        preferences: Dict[str, Any],
        properties: List[Dict[str, Any]]
    ) -> Dict[str, str]:
        """Generate AI response using OpenAI"""
        
        # Build context about user preferences
        prefs_context = "Current user preferences:\n"
        for pref_type, pref_data in preferences.items():
            confidence = pref_data["confidence"]
            explicit = "explicitly stated" if pref_data["is_explicit"] else "inferred"
            prefs_context += f"- {pref_type}: {pref_data['value']} (confidence: {confidence:.2f}, {explicit})\n"
        
        # Build context about found properties
        properties_context = ""
        if properties:
            properties_context = f"\nFound {len(properties)} relevant properties. Consider mentioning the most suitable ones in your response."
        
        messages = [
            {"role": "system", "content": self.system_prompt + "\n\n" + prefs_context + properties_context}
        ]
        
        # Add conversation history
        messages.extend(history[-10:])  # Last 10 messages for context
        
        # Add current message
        messages.append({"role": "user", "content": message})
        
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=messages,
                max_tokens=500,
                temperature=0.7
            )
            
            return {"content": response.choices[0].message.content}
            
        except Exception as e:
            return {"content": "I apologize, but I'm having trouble generating a response right now. Please try again."}

    async def _generate_recommendations(
        self, 
        user_id: int, 
        properties: List[Dict[str, Any]], 
        preferences: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate property recommendations with AI analysis"""
        recommendations = []
        
        for prop in properties[:5]:  # Top 5 properties
            try:
                # Generate AI analysis for this property
                analysis_prompt = f"""
                Analyze this property for a user with these preferences:
                {json.dumps(preferences, indent=2)}
                
                Property:
                {json.dumps(prop, indent=2)}
                
                Provide:
                1. Relevance score (0-1)
                2. 3-5 specific pros based on user preferences
                3. 3-5 specific cons or considerations
                4. Brief reasoning for the recommendation
                
                Format as JSON:
                {{
                    "relevance_score": 0.85,
                    "pros": ["specific pro 1", "specific pro 2"],
                    "cons": ["specific con 1", "specific con 2"],
                    "reasoning": "brief explanation"
                }}
                """
                
                response = self.openai_client.chat.completions.create(
                    model="gpt-4",
                    messages=[{"role": "user", "content": analysis_prompt}],
                    max_tokens=300,
                    temperature=0.3
                )
                
                analysis = json.loads(response.choices[0].message.content)
                
                recommendations.append({
                    "property": prop,
                    "relevance_score": analysis["relevance_score"],
                    "pros": analysis["pros"],
                    "cons": analysis["cons"],
                    "reasoning": analysis["reasoning"]
                })
                
            except Exception as e:
                # Fallback recommendation without AI analysis
                recommendations.append({
                    "property": prop,
                    "relevance_score": 0.5,
                    "pros": ["Matches your search criteria"],
                    "cons": ["Requires further evaluation"],
                    "reasoning": "Basic match based on search criteria"
                })
        
        # Sort by relevance score
        recommendations.sort(key=lambda x: x["relevance_score"], reverse=True)
        
        return recommendations 