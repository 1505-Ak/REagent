# REAgent - AI-Powered Real Estate Concierge

REAgent is an agentic AI-powered real estate concierge that simplifies the property search process through intelligent, autonomous interaction. 

## Features

🏠 **Natural Language Property Search** - Describe your ideal home in conversational language  
🧠 **Dynamic Preference Learning** - Learns and adapts to your preferences from feedback  
🔄 **Real-time Listings Integration** - Fetches live data from Zoopla, Rightmove, and other platforms  
📊 **Personalized Property Summaries** - Highlights pros/cons based on your priorities  
📅 **Autonomous Logistics** - Suggests viewing times and coordinates with estate agents  
🎯 **Goal-Driven Behavior** - Continuously refines recommendations through interaction

## Architecture

- **Agent Core**: Conversational AI with preference learning and memory
- **Platform Integrations**: Real-time data from major property platforms  
- **Web Interface**: Modern responsive UI for seamless interaction
- **Database**: Persistent storage for user preferences and interaction history

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env

# Run the application
python -m uvicorn app.main:app --reload
```

## Tech Stack

- **Backend**: FastAPI, SQLAlchemy, Pydantic
- **AI/ML**: OpenAI GPT-4, LangChain, Custom preference learning
- **Frontend**: Modern HTML/CSS/JavaScript with responsive design
- **Database**: SQLite (development) / PostgreSQL (production)
- **Integrations**: Zoopla API, Rightmove scraping, Google Maps API

## Development

REAgent is designed with modularity and extensibility in mind. The agent system is built to be autonomous and adaptive, learning from each user interaction to provide increasingly personalized recommendations.

## License

MIT License - see LICENSE file for details 