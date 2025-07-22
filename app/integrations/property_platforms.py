from typing import List, Dict, Any, Optional
import asyncio
import aiohttp
import requests
from bs4 import BeautifulSoup
import json
import time
from urllib.parse import urlencode

from app.core.config import get_settings


class PropertyPlatformManager:
    """
    Manages integrations with multiple property platforms to fetch real-time listings.
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.zoopla_client = ZooplaClient(self.settings.zoopla_api_key)
        self.rightmove_client = RightmoveClient()
    
    async def search_properties(self, criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Search properties across all platforms and return combined results.
        """
        tasks = []
        
        # Search Zoopla
        if self.settings.zoopla_api_key:
            tasks.append(self.zoopla_client.search_properties(criteria))
        
        # Search Rightmove (via scraping)
        tasks.append(self.rightmove_client.search_properties(criteria))
        
        # Execute searches in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Combine and deduplicate results
        all_properties = []
        for result in results:
            if isinstance(result, list):
                all_properties.extend(result)
        
        # Remove duplicates based on address and price
        unique_properties = self._deduplicate_properties(all_properties)
        
        # Sort by relevance score if available, otherwise by price
        unique_properties.sort(
            key=lambda x: (x.get('relevance_score', 0), -x.get('price', 0)), 
            reverse=True
        )
        
        return unique_properties[:20]  # Return top 20 results
    
    def _deduplicate_properties(self, properties: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate properties based on location and price"""
        seen = set()
        unique = []
        
        for prop in properties:
            # Create a key based on location and price for deduplication
            key = (
                prop.get('location', '').lower().strip(),
                prop.get('price', 0),
                prop.get('bedrooms', 0)
            )
            
            if key not in seen:
                seen.add(key)
                unique.append(prop)
        
        return unique


class ZooplaClient:
    """
    Zoopla API client for fetching property listings.
    """
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.zoopla.co.uk/api/v1"
        self.session = None
    
    async def search_properties(self, criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Search properties using Zoopla API"""
        if not self.api_key:
            return []
        
        try:
            params = self._build_zoopla_params(criteria)
            
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/property_listings.json"
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self._parse_zoopla_results(data)
                    else:
                        print(f"Zoopla API error: {response.status}")
                        return []
        
        except Exception as e:
            print(f"Zoopla search error: {e}")
            return []
    
    def _build_zoopla_params(self, criteria: Dict[str, Any]) -> Dict[str, str]:
        """Build Zoopla API parameters from search criteria"""
        params = {
            'api_key': self.api_key,
            'listing_status': 'sale',
            'page_size': '10'
        }
        
        if 'location' in criteria:
            params['area'] = criteria['location']
        
        if 'max_price' in criteria:
            params['maximum_price'] = str(criteria['max_price'])
        
        if 'min_price' in criteria:
            params['minimum_price'] = str(criteria['min_price'])
        
        if 'min_bedrooms' in criteria:
            params['minimum_beds'] = str(criteria['min_bedrooms'])
        
        if 'max_bedrooms' in criteria:
            params['maximum_beds'] = str(criteria['max_bedrooms'])
        
        if 'property_type' in criteria:
            # Map property types to Zoopla format
            prop_type_mapping = {
                'house': 'houses',
                'flat': 'flats',
                'apartment': 'flats'
            }
            if criteria['property_type'].lower() in prop_type_mapping:
                params['property_type'] = prop_type_mapping[criteria['property_type'].lower()]
        
        return params
    
    def _parse_zoopla_results(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse Zoopla API response into standardized format"""
        properties = []
        
        listings = data.get('listing', [])
        
        for listing in listings:
            try:
                property_data = {
                    'external_id': str(listing.get('listing_id', '')),
                    'platform': 'zoopla',
                    'title': listing.get('displayable_address', ''),
                    'description': listing.get('description', ''),
                    'price': listing.get('price', 0),
                    'bedrooms': listing.get('num_bedrooms', 0),
                    'bathrooms': listing.get('num_bathrooms', 0),
                    'property_type': listing.get('property_type', ''),
                    'location': listing.get('displayable_address', ''),
                    'postcode': listing.get('outcode', ''),
                    'latitude': listing.get('latitude'),
                    'longitude': listing.get('longitude'),
                    'images': [listing.get('image_url')] if listing.get('image_url') else [],
                    'features': self._extract_features(listing),
                    'agent_info': {
                        'name': listing.get('agent_name', ''),
                        'phone': listing.get('agent_phone', ''),
                        'logo': listing.get('agent_logo', '')
                    },
                    'url': listing.get('details_url', ''),
                    'last_published_date': listing.get('last_published_date', ''),
                    'relevance_score': 0.8  # Default relevance for API results
                }
                
                properties.append(property_data)
                
            except Exception as e:
                print(f"Error parsing Zoopla listing: {e}")
                continue
        
        return properties
    
    def _extract_features(self, listing: Dict[str, Any]) -> List[str]:
        """Extract property features from Zoopla listing"""
        features = []
        
        # Add basic features
        if listing.get('num_floors'):
            features.append(f"{listing['num_floors']} floors")
        
        if listing.get('property_type'):
            features.append(listing['property_type'])
        
        # Add descriptive features from description
        description = listing.get('description', '').lower()
        feature_keywords = ['garden', 'parking', 'garage', 'balcony', 'terrace', 'ensuite']
        
        for keyword in feature_keywords:
            if keyword in description:
                features.append(keyword.title())
        
        return features


class RightmoveClient:
    """
    Rightmove client using web scraping (since they don't have a public API).
    """
    
    def __init__(self):
        self.base_url = "https://www.rightmove.co.uk"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
    
    async def search_properties(self, criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Search properties on Rightmove using web scraping"""
        try:
            search_url = self._build_rightmove_url(criteria)
            
            async with aiohttp.ClientSession() as session:
                async with session.get(search_url, headers=self.headers) as response:
                    if response.status == 200:
                        html = await response.text()
                        return self._parse_rightmove_results(html)
                    else:
                        print(f"Rightmove request failed: {response.status}")
                        return []
        
        except Exception as e:
            print(f"Rightmove search error: {e}")
            return []
    
    def _build_rightmove_url(self, criteria: Dict[str, Any]) -> str:
        """Build Rightmove search URL from criteria"""
        params = {
            'searchType': 'SALE',
            'locationIdentifier': self._get_location_identifier(criteria.get('location', 'London')),
            'includeSSTC': 'false'
        }
        
        if 'max_price' in criteria:
            params['maxPrice'] = str(criteria['max_price'])
        
        if 'min_price' in criteria:
            params['minPrice'] = str(criteria['min_price'])
        
        if 'min_bedrooms' in criteria:
            params['minBedrooms'] = str(criteria['min_bedrooms'])
        
        if 'max_bedrooms' in criteria:
            params['maxBedrooms'] = str(criteria['max_bedrooms'])
        
        if 'property_type' in criteria:
            # Map to Rightmove property types
            prop_type_mapping = {
                'house': 'houses',
                'flat': 'flats',
                'apartment': 'flats'
            }
            if criteria['property_type'].lower() in prop_type_mapping:
                params['propertyTypes'] = prop_type_mapping[criteria['property_type'].lower()]
        
        query_string = urlencode(params)
        return f"{self.base_url}/property-for-sale/find.html?{query_string}"
    
    def _get_location_identifier(self, location: str) -> str:
        """Get Rightmove location identifier (simplified)"""
        # This is a simplified version - in production, you'd need to call
        # Rightmove's location search API to get proper identifiers
        location_mapping = {
            'london': 'REGION^876',
            'manchester': 'REGION^775',
            'birmingham': 'REGION^774'
        }
        
        location_lower = location.lower()
        for key, value in location_mapping.items():
            if key in location_lower:
                return value
        
        return 'REGION^876'  # Default to London
    
    def _parse_rightmove_results(self, html: str) -> List[Dict[str, Any]]:
        """Parse Rightmove HTML response"""
        properties = []
        
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Find property cards
            property_cards = soup.find_all('div', class_='l-searchResult')
            
            for card in property_cards[:10]:  # Limit to 10 results
                try:
                    property_data = self._extract_property_from_card(card)
                    if property_data:
                        properties.append(property_data)
                except Exception as e:
                    print(f"Error parsing Rightmove property card: {e}")
                    continue
        
        except Exception as e:
            print(f"Error parsing Rightmove HTML: {e}")
        
        return properties
    
    def _extract_property_from_card(self, card) -> Optional[Dict[str, Any]]:
        """Extract property data from a Rightmove property card"""
        try:
            # Extract basic information
            price_elem = card.find('span', class_='propertyCard-priceValue')
            price = self._parse_price_text(price_elem.text if price_elem else '0')
            
            address_elem = card.find('address', class_='propertyCard-address')
            address = address_elem.text.strip() if address_elem else ''
            
            description_elem = card.find('span', class_='propertyCard-description')
            description = description_elem.text.strip() if description_elem else ''
            
            # Extract property details
            details = card.find('h2', class_='propertyCard-title')
            bedrooms = self._extract_bedrooms(details.text if details else '')
            
            # Extract image
            img_elem = card.find('img', class_='propertyCard-img')
            image_url = img_elem.get('src', '') if img_elem else ''
            
            # Extract property URL
            link_elem = card.find('a', class_='propertyCard-link')
            property_url = self.base_url + link_elem.get('href', '') if link_elem else ''
            
            return {
                'external_id': property_url.split('/')[-1] if property_url else '',
                'platform': 'rightmove',
                'title': address,
                'description': description,
                'price': price,
                'bedrooms': bedrooms,
                'bathrooms': 0,  # Not easily extractable from cards
                'property_type': self._extract_property_type(description),
                'location': address,
                'postcode': self._extract_postcode(address),
                'latitude': None,
                'longitude': None,
                'images': [image_url] if image_url else [],
                'features': self._extract_features_from_description(description),
                'agent_info': {},
                'url': property_url,
                'relevance_score': 0.7  # Default relevance for scraped results
            }
        
        except Exception as e:
            print(f"Error extracting property data: {e}")
            return None
    
    def _parse_price_text(self, price_text: str) -> int:
        """Parse price text to integer"""
        try:
            # Remove £, commas, and other characters
            price_clean = ''.join(c for c in price_text if c.isdigit())
            return int(price_clean) if price_clean else 0
        except:
            return 0
    
    def _extract_bedrooms(self, title_text: str) -> int:
        """Extract number of bedrooms from title"""
        import re
        match = re.search(r'(\d+)\s*bed', title_text.lower())
        return int(match.group(1)) if match else 0
    
    def _extract_property_type(self, description: str) -> str:
        """Extract property type from description"""
        description_lower = description.lower()
        if 'flat' in description_lower or 'apartment' in description_lower:
            return 'flat'
        elif 'house' in description_lower:
            return 'house'
        elif 'studio' in description_lower:
            return 'studio'
        else:
            return 'property'
    
    def _extract_postcode(self, address: str) -> str:
        """Extract postcode from address"""
        import re
        # UK postcode pattern
        postcode_pattern = r'[A-Z]{1,2}[0-9R][0-9A-Z]? [0-9][A-Z]{2}'
        match = re.search(postcode_pattern, address.upper())
        return match.group(0) if match else ''
    
    def _extract_features_from_description(self, description: str) -> List[str]:
        """Extract features from property description"""
        features = []
        description_lower = description.lower()
        
        feature_keywords = ['garden', 'parking', 'garage', 'balcony', 'terrace', 'ensuite', 'modern', 'Victorian', 'new build']
        
        for keyword in feature_keywords:
            if keyword in description_lower:
                features.append(keyword.title())
        
        return features 