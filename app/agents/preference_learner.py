from typing import List, Dict, Any, Optional
import re
import json
from sqlalchemy.orm import Session
from openai import OpenAI

from app.core.config import get_settings
from app.database.models import UserPreference


class PreferenceLearner:
    """
    Intelligent preference learning system that extracts user preferences from natural
    language conversation and updates them with confidence scoring.
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.settings = get_settings()
        self.openai_client = OpenAI(api_key=self.settings.openai_api_key)
        
        # Preference extraction prompt
        self.extraction_prompt = """
        You are an expert at extracting property search preferences from natural language.
        
        Extract preferences from the user message and classify them into these categories:
        
        - location: specific areas, cities, postcodes, or regions
        - max_price: maximum budget (extract numbers, convert to integer)
        - min_price: minimum budget  
        - min_bedrooms: minimum number of bedrooms
        - max_bedrooms: maximum number of bedrooms
        - property_type: house, flat, apartment, studio, bungalow, etc.
        - garden: yes, no, or specific requirements
        - parking: yes, no, or specific requirements
        - transport_links: proximity to stations, bus routes
        - schools: proximity to good schools
        - lifestyle: quiet area, vibrant area, family-friendly, etc.
        - move_date: when they want to move
        - specific_features: balcony, ensuite, modern kitchen, etc.
        
        For each preference:
        1. Determine if it's explicitly stated or implied
        2. Assign confidence score (0.1-1.0):
           - 1.0: explicitly stated with certainty
           - 0.8: clearly mentioned  
           - 0.6: strongly implied
           - 0.4: weakly implied
           - 0.2: very uncertain inference
        
        Return JSON format:
        {
            "preferences": [
                {
                    "type": "location",
                    "value": "London",
                    "confidence": 0.9,
                    "is_explicit": true,
                    "context": "User said 'looking in London'"
                }
            ]
        }
        
        If no clear preferences are found, return empty preferences array.
        """

    async def extract_preferences(self, message: str, user_id: int) -> List[Dict[str, Any]]:
        """
        Extract preferences from a user message and update the database.
        """
        try:
            # Use OpenAI to extract preferences
            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": self.extraction_prompt},
                    {"role": "user", "content": f"Extract preferences from: '{message}'"}
                ],
                max_tokens=500,
                temperature=0.1  # Low temperature for consistent extraction
            )
            
            # Parse the response
            result = json.loads(response.choices[0].message.content)
            extracted_preferences = result.get("preferences", [])
            
            # Update database with extracted preferences
            for pref in extracted_preferences:
                self._update_user_preference(
                    user_id=user_id,
                    preference_type=pref["type"],
                    preference_value=pref["value"],
                    confidence_score=pref["confidence"],
                    is_explicit=pref["is_explicit"]
                )
            
            return extracted_preferences
            
        except Exception as e:
            print(f"Error extracting preferences: {e}")
            # Fallback to simple keyword matching
            return self._fallback_extraction(message, user_id)

    def _update_user_preference(
        self, 
        user_id: int, 
        preference_type: str, 
        preference_value: str,
        confidence_score: float,
        is_explicit: bool
    ):
        """
        Update or create a user preference with intelligent merging.
        """
        # Check if preference already exists
        existing_pref = (
            self.db.query(UserPreference)
            .filter(
                UserPreference.user_id == user_id,
                UserPreference.preference_type == preference_type
            )
            .first()
        )
        
        if existing_pref:
            # Intelligent merging logic
            if confidence_score > existing_pref.confidence_score:
                # New preference has higher confidence, replace
                existing_pref.preference_value = preference_value
                existing_pref.confidence_score = confidence_score
                existing_pref.is_explicit = is_explicit
            elif confidence_score == existing_pref.confidence_score and is_explicit:
                # Same confidence but explicit, replace
                existing_pref.preference_value = preference_value
                existing_pref.is_explicit = is_explicit
            else:
                # Keep existing preference but potentially merge values
                merged_value = self._merge_preference_values(
                    existing_pref.preference_value, 
                    preference_value,
                    preference_type
                )
                if merged_value != existing_pref.preference_value:
                    existing_pref.preference_value = merged_value
                    existing_pref.confidence_score = max(existing_pref.confidence_score, confidence_score)
        else:
            # Create new preference
            new_pref = UserPreference(
                user_id=user_id,
                preference_type=preference_type,
                preference_value=preference_value,
                confidence_score=confidence_score,
                is_explicit=is_explicit
            )
            self.db.add(new_pref)
        
        self.db.commit()

    def _merge_preference_values(self, existing: str, new: str, pref_type: str) -> str:
        """
        Intelligently merge preference values based on type.
        """
        if pref_type == "location":
            # For locations, keep the more specific one or combine
            if len(new) > len(existing):
                return new  # Assume longer is more specific
            return existing
        
        elif pref_type in ["max_price", "min_price"]:
            # For prices, take the more recent/explicit one
            return new
        
        elif pref_type in ["min_bedrooms", "max_bedrooms"]:
            # For bedrooms, take the more recent one
            return new
        
        elif pref_type == "specific_features":
            # Combine features
            existing_features = existing.split(", ") if existing else []
            new_features = new.split(", ") if new else []
            combined = list(set(existing_features + new_features))
            return ", ".join(combined)
        
        else:
            # Default: return new value
            return new

    def _fallback_extraction(self, message: str, user_id: int) -> List[Dict[str, Any]]:
        """
        Fallback preference extraction using simple pattern matching.
        """
        extracted = []
        message_lower = message.lower()
        
        # Location patterns
        location_patterns = [
            r'in ([a-zA-Z\s]+)',
            r'around ([a-zA-Z\s]+)',
            r'near ([a-zA-Z\s]+)'
        ]
        for pattern in location_patterns:
            match = re.search(pattern, message_lower)
            if match:
                location = match.group(1).strip()
                if len(location) > 2:
                    extracted.append({
                        "type": "location",
                        "value": location.title(),
                        "confidence": 0.6,
                        "is_explicit": True,
                        "context": f"Pattern match: {match.group(0)}"
                    })
                    break
        
        # Price patterns
        price_patterns = [
            r'under £?(\d+(?:,\d{3})*(?:k)?)',
            r'max.*?£?(\d+(?:,\d{3})*(?:k)?)',
            r'budget.*?£?(\d+(?:,\d{3})*(?:k)?)'
        ]
        for pattern in price_patterns:
            match = re.search(pattern, message_lower)
            if match:
                price_str = match.group(1)
                price = self._parse_price(price_str)
                if price:
                    extracted.append({
                        "type": "max_price",
                        "value": str(price),
                        "confidence": 0.7,
                        "is_explicit": True,
                        "context": f"Pattern match: {match.group(0)}"
                    })
                    break
        
        # Bedroom patterns
        bedroom_patterns = [
            r'(\d+)\s*bed',
            r'(\d+)\s*bedroom'
        ]
        for pattern in bedroom_patterns:
            match = re.search(pattern, message_lower)
            if match:
                bedrooms = match.group(1)
                extracted.append({
                    "type": "min_bedrooms",
                    "value": bedrooms,
                    "confidence": 0.8,
                    "is_explicit": True,
                    "context": f"Pattern match: {match.group(0)}"
                })
                break
        
        # Property type patterns
        property_types = ["house", "flat", "apartment", "studio", "bungalow", "cottage"]
        for prop_type in property_types:
            if prop_type in message_lower:
                extracted.append({
                    "type": "property_type",
                    "value": prop_type,
                    "confidence": 0.9,
                    "is_explicit": True,
                    "context": f"Direct mention of {prop_type}"
                })
                break
        
        # Update database with fallback extractions
        for pref in extracted:
            self._update_user_preference(
                user_id=user_id,
                preference_type=pref["type"],
                preference_value=pref["value"],
                confidence_score=pref["confidence"],
                is_explicit=pref["is_explicit"]
            )
        
        return extracted

    def _parse_price(self, price_str: str) -> Optional[int]:
        """Parse price string to integer"""
        try:
            # Remove commas and convert k to thousands
            price_str = price_str.replace(',', '')
            if price_str.endswith('k'):
                return int(price_str[:-1]) * 1000
            return int(price_str)
        except:
            return None

    def get_user_preferences_summary(self, user_id: int) -> str:
        """
        Generate a natural language summary of user preferences.
        """
        preferences = (
            self.db.query(UserPreference)
            .filter(UserPreference.user_id == user_id)
            .all()
        )
        
        if not preferences:
            return "No preferences learned yet."
        
        summary_parts = []
        for pref in preferences:
            confidence_text = "confidently" if pref.confidence_score > 0.7 else "tentatively"
            explicit_text = "explicitly stated" if pref.is_explicit else "inferred"
            
            summary_parts.append(
                f"{pref.preference_type}: {pref.preference_value} "
                f"({confidence_text}, {explicit_text})"
            )
        
        return "User preferences: " + "; ".join(summary_parts) 