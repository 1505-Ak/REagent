# REAgent - AI-Powered Real Estate Concierge

REAgent is an agentic AI-powered real estate concierge that simplifies the property search process through intelligent, autonomous interaction. 

## 🌟 Features

🏠 **Natural Language Property Search** - Describe your ideal home in conversational language  
🧠 **Dynamic Preference Learning** - Learns and adapts to your preferences from feedback  
🔄 **Real-time Listings Integration** - Fetches live data from Zoopla, Rightmove, and other platforms  
📊 **Personalized Property Summaries** - Highlights pros/cons based on your priorities  
📅 **Autonomous Logistics** - Suggests viewing times and coordinates with estate agents  
🎯 **Goal-Driven Behavior** - Continuously refines recommendations through interaction  
🎨 **Beautiful Modern UI** - Responsive chat interface with real-time property cards  

## 🚀 Quick Start

### 1. Clone and Install

```bash
git clone https://github.com/1505-Ak/REagent.git
cd REagent
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
python run.py
# This will create a .env file template
```

Edit the `.env` file and add your OpenAI API key:
```env
OPENAI_API_KEY=your_actual_openai_api_key_here
```

> 🔑 **Get your OpenAI API key**: https://platform.openai.com/api-keys

### 3. Test Installation

```bash
python test_reagent.py
```

### 4. Start REAgent

```bash
python run.py
```

🌐 **Open your browser**: http://localhost:8000

## 💬 How to Use

1. **Start Chatting**: Simply describe what you're looking for
   - "I need a 2-bedroom flat in London under £500k"
   - "Find me a family house with a garden in Manchester"
   - "Looking for a modern apartment near good transport links"

2. **Refine Your Search**: REAgent learns from your feedback
   - "Actually, I prefer houses over flats"
   - "Show me something with a larger garden"
   - "I need better transport connections"

3. **View Recommendations**: Property cards appear in the sidebar
   - Click any property for detailed information
   - See personalized pros/cons based on your preferences
   - Direct links to original listings

4. **Track Learning**: View your learned preferences
   - Click "Preferences" to see what REAgent has learned
   - See confidence scores and preference categories
   - Understand how your ideal home profile is built

## 🏗️ Architecture

```
REAgent/
├── app/
│   ├── main.py                 # FastAPI application entry point
│   ├── agents/                 # AI agent system
│   │   ├── core_agent.py      # Main conversational agent
│   │   └── preference_learner.py # Dynamic preference extraction
│   ├── api/                    # REST API endpoints
│   │   ├── chat.py            # Chat and conversation management
│   │   ├── properties.py      # Property search and details
│   │   └── preferences.py     # Preference management
│   ├── database/              # Data models and storage
│   │   ├── models.py         # SQLAlchemy models
│   │   └── database.py       # Database configuration
│   ├── integrations/          # External platform connectors
│   │   └── property_platforms.py # Zoopla, Rightmove integration
│   ├── templates/             # HTML templates
│   │   └── index.html        # Main web interface
│   └── static/               # CSS and JavaScript assets
│       ├── css/styles.css    # Modern responsive design
│       └── js/app.js         # Interactive chat application
├── requirements.txt          # Python dependencies
├── run.py                   # Quick start script
└── test_reagent.py         # Basic functionality tests
```

## 🔧 Configuration

### Required Settings

- **OPENAI_API_KEY**: Your OpenAI API key (required for AI features)

### Optional Settings

- **ZOOPLA_API_KEY**: Zoopla API key for live property data
- **RIGHTMOVE_API_KEY**: Rightmove API access (when available)
- **DATABASE_URL**: Database connection (defaults to SQLite)

### Environment Variables

```env
# AI Configuration
OPENAI_API_KEY=your_openai_api_key_here

# Database
DATABASE_URL=sqlite:///./reagent.db

# Property Platforms (Optional)
ZOOPLA_API_KEY=your_zoopla_api_key_here
RIGHTMOVE_API_KEY=your_rightmove_api_key_here

# Application
SECRET_KEY=your-secret-key-here
ENVIRONMENT=development
LOG_LEVEL=INFO
```

## 🧠 How REAgent Works

### 1. Conversational AI
- Powered by OpenAI GPT-4 for natural language understanding
- Maintains conversation context and user history
- Provides warm, professional, and helpful responses

### 2. Dynamic Preference Learning
- Extracts preferences from natural language using AI
- Assigns confidence scores to learned preferences
- Distinguishes between explicit and inferred preferences
- Continuously updates and refines user profile

### 3. Intelligent Property Matching
- Searches multiple property platforms simultaneously
- Ranks properties based on learned preferences
- Generates personalized pros/cons for each property
- Provides relevance scores for recommendations

### 4. Autonomous Behavior
- Proactively asks clarifying questions
- Suggests next steps and viewing arrangements
- Learns from user feedback to improve recommendations
- Adapts conversation style to user preferences

## 📊 API Documentation

When running locally, visit:
- **Interactive API Docs**: http://localhost:8000/docs
- **ReDoc Documentation**: http://localhost:8000/redoc

### Key Endpoints

- `POST /api/chat/message` - Send message to REAgent
- `GET /api/chat/history/{session_id}` - Get conversation history
- `POST /api/properties/search` - Search properties
- `GET /api/preferences/{session_id}` - Get learned preferences
- `GET /api/preferences/{session_id}/insights` - Get preference analytics

## 🎨 Design Philosophy

### User Experience
- **Conversational First**: Natural language is the primary interface
- **Progressive Disclosure**: Information revealed as needed
- **Instant Feedback**: Real-time responses and property updates
- **Mobile Responsive**: Works seamlessly on all devices

### AI Design
- **Autonomous**: Makes decisions and suggestions independently
- **Adaptive**: Learns and improves with each interaction
- **Transparent**: Shows confidence and reasoning
- **Goal-Oriented**: Focused on finding the perfect home

## 🔒 Privacy & Security

- **Session-Based**: No user accounts required
- **Local Storage**: Data stored locally by default
- **Configurable**: Can be configured for any database
- **API Key Security**: Secure handling of external API keys

## 🚀 Deployment

### Development
```bash
python run.py
```

### Production
```bash
pip install -r requirements.txt
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Docker (Optional)
```dockerfile
# Example Dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## 🧪 Testing

Run the test suite:
```bash
python test_reagent.py
```

Run with pytest:
```bash
pip install pytest
pytest test_reagent.py -v
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## 📝 License

MIT License - see LICENSE file for details

## 🆘 Support

- **Documentation**: Check this README and API docs
- **Issues**: Open a GitHub issue for bugs or feature requests
- **Testing**: Run `python test_reagent.py` to diagnose problems

## 🔮 Future Enhancements

- **Multi-Language Support**: Support for multiple languages
- **Advanced Filters**: More sophisticated search criteria
- **Market Analytics**: Property market trends and insights
- **Virtual Tours**: Integration with 360° property tours
- **Mortgage Calculator**: Built-in affordability calculations
- **Area Insights**: Neighborhood information and scoring

---

**Made with ❤️ for finding the perfect home** 