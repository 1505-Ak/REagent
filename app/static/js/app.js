// REAgent JavaScript Application
class REAgentApp {
    constructor() {
        this.sessionId = this.getOrCreateSessionId();
        this.isLoading = false;
        this.currentRecommendations = [];
        this.currentPreferences = {};
        
        this.initializeEventListeners();
        this.loadConversationHistory();
    }

    // Session Management
    getOrCreateSessionId() {
        let sessionId = localStorage.getItem('reagent_session_id');
        if (!sessionId) {
            sessionId = 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
            localStorage.setItem('reagent_session_id', sessionId);
        }
        return sessionId;
    }

    // Event Listeners
    initializeEventListeners() {
        // Chat input and send button
        const messageInput = document.getElementById('messageInput');
        const sendBtn = document.getElementById('sendBtn');
        
        messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });
        
        sendBtn.addEventListener('click', () => this.sendMessage());
        
        // Quick starter buttons
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('starter-btn')) {
                const message = e.target.textContent.replace(/"/g, '');
                messageInput.value = message;
                this.sendMessage();
            }
        });
        
        // Header buttons
        document.getElementById('preferencesBtn').addEventListener('click', () => {
            this.showPreferencesModal();
        });
        
        document.getElementById('clearChatBtn').addEventListener('click', () => {
            this.clearChat();
        });
        
        // Modal handlers
        document.getElementById('closePreferencesModal').addEventListener('click', () => {
            this.hideModal('preferencesModal');
        });
        
        document.getElementById('closePropertyModal').addEventListener('click', () => {
            this.hideModal('propertyModal');
        });
        
        // Click outside modal to close
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('modal')) {
                this.hideModal(e.target.id);
            }
        });
        
        // Property card clicks
        document.addEventListener('click', (e) => {
            const propertyCard = e.target.closest('.property-card');
            if (propertyCard) {
                const propertyId = propertyCard.dataset.propertyId;
                const platform = propertyCard.dataset.platform;
                this.showPropertyDetails(propertyId, platform);
            }
        });
    }

    // Chat Functions
    async sendMessage() {
        const messageInput = document.getElementById('messageInput');
        const message = messageInput.value.trim();
        
        if (!message || this.isLoading) return;
        
        // Add user message to chat
        this.addMessageToChat(message, 'user');
        messageInput.value = '';
        
        // Show typing indicator
        this.showTypingIndicator();
        
        try {
            const response = await fetch('/api/chat/message', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    message: message,
                    session_id: this.sessionId
                })
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            
            // Hide typing indicator
            this.hideTypingIndicator();
            
            // Add agent response to chat
            this.addMessageToChat(data.response, 'agent');
            
            // Update recommendations
            if (data.recommendations && data.recommendations.length > 0) {
                this.updateRecommendations(data.recommendations);
            }
            
            // Update preferences display
            if (data.extracted_preferences && data.extracted_preferences.length > 0) {
                this.loadPreferences();
            }
            
        } catch (error) {
            console.error('Error sending message:', error);
            this.hideTypingIndicator();
            this.addMessageToChat('Sorry, I encountered an error. Please try again.', 'agent');
        }
    }

    addMessageToChat(message, sender) {
        const chatMessages = document.getElementById('chatMessages');
        const timestamp = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}-message`;
        
        const avatarIcon = sender === 'agent' ? 'fas fa-robot' : 'fas fa-user';
        const senderName = sender === 'agent' ? 'REAgent' : 'You';
        
        messageDiv.innerHTML = `
            <div class="message-avatar">
                <i class="${avatarIcon}"></i>
            </div>
            <div class="message-content">
                <div class="message-header">
                    <span class="sender">${senderName}</span>
                    <span class="timestamp">${timestamp}</span>
                </div>
                <div class="message-text">
                    <p>${this.formatMessage(message)}</p>
                </div>
            </div>
        `;
        
        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
        
        // Remove welcome message if this is the first user message
        if (sender === 'user' && document.querySelector('.welcome-message')) {
            document.querySelector('.welcome-message').remove();
        }
    }

    formatMessage(message) {
        // Simple formatting - convert URLs to links, etc.
        return message
            .replace(/\n/g, '<br>')
            .replace(/(https?:\/\/[^\s]+)/g, '<a href="$1" target="_blank" rel="noopener">$1</a>');
    }

    showTypingIndicator() {
        document.getElementById('typingIndicator').style.display = 'flex';
        this.isLoading = true;
        document.getElementById('sendBtn').disabled = true;
    }

    hideTypingIndicator() {
        document.getElementById('typingIndicator').style.display = 'none';
        this.isLoading = false;
        document.getElementById('sendBtn').disabled = false;
    }

    // Recommendations
    updateRecommendations(recommendations) {
        this.currentRecommendations = recommendations;
        const container = document.getElementById('recommendationsContainer');
        const countBadge = document.getElementById('recommendationCount');
        
        countBadge.textContent = recommendations.length;
        
        if (recommendations.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-search"></i>
                    <p>No recommendations yet. Keep chatting to get personalized suggestions!</p>
                </div>
            `;
            return;
        }
        
        container.innerHTML = '';
        
        recommendations.forEach((rec, index) => {
            const property = rec.property || rec;
            const card = document.createElement('div');
            card.className = 'property-card';
            card.dataset.propertyId = property.external_id || property.id;
            card.dataset.platform = property.platform || 'unknown';
            
            const price = this.formatPrice(property.price);
            const bedrooms = property.bedrooms ? `${property.bedrooms} bed` : '';
            const propertyType = property.property_type || 'Property';
            
            card.innerHTML = `
                <div class="property-header">
                    <div class="property-title">${property.title || property.location}</div>
                    <div class="property-price">${price}</div>
                </div>
                <div class="property-location">${property.location}</div>
                <div class="property-details">
                    <span>${bedrooms}</span>
                    <span>${propertyType}</span>
                </div>
                ${rec.relevance_score ? `
                    <div class="relevance-score">
                        <i class="fas fa-star"></i>
                        ${Math.round(rec.relevance_score * 100)}% match
                    </div>
                ` : ''}
            `;
            
            container.appendChild(card);
        });
    }

    formatPrice(price) {
        if (!price) return 'POA';
        
        if (price >= 1000000) {
            return `£${(price / 1000000).toFixed(1)}M`;
        } else if (price >= 1000) {
            return `£${(price / 1000).toFixed(0)}k`;
        } else {
            return `£${price.toLocaleString()}`;
        }
    }

    // Preferences
    async loadPreferences() {
        try {
            const response = await fetch(`/api/preferences/${this.sessionId}`);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            this.currentPreferences = data.preferences;
            this.updatePreferencesDisplay(data.preferences);
            
        } catch (error) {
            console.error('Error loading preferences:', error);
        }
    }

    updatePreferencesDisplay(preferences) {
        const container = document.getElementById('preferencesContainer');
        
        if (Object.keys(preferences).length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-lightbulb"></i>
                    <p>I'll learn your preferences as we chat</p>
                </div>
            `;
            return;
        }
        
        container.innerHTML = '';
        
        Object.entries(preferences).forEach(([type, pref]) => {
            const item = document.createElement('div');
            item.className = 'preference-item';
            
            const confidencePercent = Math.round(pref.confidence_score * 100);
            const confidenceWidth = `${confidencePercent}%`;
            
            item.innerHTML = `
                <div class="preference-type">${type.replace(/_/g, ' ')}</div>
                <div class="preference-value">${pref.value}</div>
                <div class="preference-meta">
                    <span>${pref.is_explicit ? 'Explicit' : 'Inferred'}</span>
                    <div class="confidence-bar">
                        <div class="confidence-fill" style="width: ${confidenceWidth}"></div>
                    </div>
                </div>
            `;
            
            container.appendChild(item);
        });
    }

    // Modals
    async showPreferencesModal() {
        try {
            const response = await fetch(`/api/preferences/${this.sessionId}/insights`);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            this.displayPreferenceInsights(data);
            this.showModal('preferencesModal');
            
        } catch (error) {
            console.error('Error loading preference insights:', error);
        }
    }

    displayPreferenceInsights(data) {
        const container = document.getElementById('insightsContainer');
        
        container.innerHTML = `
            <div class="insights-summary">
                <h3>Preference Summary</h3>
                <p>${data.insights}</p>
            </div>
            
            <div class="insights-stats">
                <div class="stat-grid">
                    <div class="stat-item">
                        <div class="stat-number">${data.total_preferences}</div>
                        <div class="stat-label">Total Preferences</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-number">${data.average_confidence}%</div>
                        <div class="stat-label">Avg Confidence</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-number">${data.explicit_preferences}</div>
                        <div class="stat-label">Explicit</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-number">${data.implicit_preferences}</div>
                        <div class="stat-label">Inferred</div>
                    </div>
                </div>
            </div>
            
            <div class="insights-categories">
                <h4>Preference Categories</h4>
                ${Object.entries(data.preference_categories || {}).map(([category, count]) => `
                    <div class="category-item">
                        <span class="category-name">${category}</span>
                        <span class="category-count">${count}</span>
                    </div>
                `).join('')}
            </div>
        `;
    }

    showModal(modalId) {
        document.getElementById(modalId).classList.add('active');
        document.body.style.overflow = 'hidden';
    }

    hideModal(modalId) {
        document.getElementById(modalId).classList.remove('active');
        document.body.style.overflow = 'auto';
    }

    // Property Details
    async showPropertyDetails(propertyId, platform) {
        // For now, show basic property info from current recommendations
        const property = this.currentRecommendations.find(rec => 
            (rec.property?.external_id || rec.property?.id) === propertyId
        );
        
        if (!property) return;
        
        const prop = property.property || property;
        const container = document.getElementById('propertyDetails');
        
        container.innerHTML = `
            <div class="property-detail-header">
                <h3>${prop.title || prop.location}</h3>
                <div class="property-price-large">${this.formatPrice(prop.price)}</div>
            </div>
            
            <div class="property-detail-info">
                <div class="detail-row">
                    <span class="detail-label">Location:</span>
                    <span class="detail-value">${prop.location}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">Type:</span>
                    <span class="detail-value">${prop.property_type || 'N/A'}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">Bedrooms:</span>
                    <span class="detail-value">${prop.bedrooms || 'N/A'}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">Bathrooms:</span>
                    <span class="detail-value">${prop.bathrooms || 'N/A'}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">Platform:</span>
                    <span class="detail-value">${prop.platform}</span>
                </div>
            </div>
            
            ${prop.description ? `
                <div class="property-description">
                    <h4>Description</h4>
                    <p>${prop.description}</p>
                </div>
            ` : ''}
            
            ${property.pros || property.cons ? `
                <div class="property-analysis">
                    ${property.pros ? `
                        <div class="pros-section">
                            <h4><i class="fas fa-thumbs-up"></i> Pros</h4>
                            <ul>
                                ${property.pros.map(pro => `<li>${pro}</li>`).join('')}
                            </ul>
                        </div>
                    ` : ''}
                    
                    ${property.cons ? `
                        <div class="cons-section">
                            <h4><i class="fas fa-thumbs-down"></i> Considerations</h4>
                            <ul>
                                ${property.cons.map(con => `<li>${con}</li>`).join('')}
                            </ul>
                        </div>
                    ` : ''}
                </div>
            ` : ''}
            
            ${prop.url ? `
                <div class="property-actions">
                    <a href="${prop.url}" target="_blank" rel="noopener" class="btn btn-primary">
                        <i class="fas fa-external-link-alt"></i> View on ${prop.platform}
                    </a>
                </div>
            ` : ''}
        `;
        
        this.showModal('propertyModal');
    }

    // Conversation History
    async loadConversationHistory() {
        try {
            const response = await fetch(`/api/chat/history/${this.sessionId}`);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            
            // Load conversations
            if (data.conversations && data.conversations.length > 0) {
                const chatMessages = document.getElementById('chatMessages');
                const welcomeMessage = chatMessages.querySelector('.welcome-message');
                
                if (welcomeMessage) {
                    welcomeMessage.remove();
                }
                
                data.conversations.forEach(conv => {
                    if (conv.message_type === 'user') {
                        this.addMessageToChat(conv.message, 'user');
                    } else if (conv.message_type === 'agent') {
                        this.addMessageToChat(conv.response, 'agent');
                    }
                });
            }
            
            // Load preferences
            this.currentPreferences = data.user_preferences || {};
            this.updatePreferencesDisplay(this.currentPreferences);
            
        } catch (error) {
            console.error('Error loading conversation history:', error);
        }
    }

    // Clear Chat
    async clearChat() {
        if (!confirm('Are you sure you want to clear the chat and start fresh? This will remove all conversation history and learned preferences.')) {
            return;
        }
        
        try {
            const response = await fetch(`/api/chat/session/${this.sessionId}`, {
                method: 'DELETE'
            });
            
            if (response.ok) {
                // Clear UI
                const chatMessages = document.getElementById('chatMessages');
                chatMessages.innerHTML = `
                    <div class="message agent-message welcome-message">
                        <div class="message-avatar">
                            <i class="fas fa-robot"></i>
                        </div>
                        <div class="message-content">
                            <div class="message-header">
                                <span class="sender">REAgent</span>
                                <span class="timestamp">Just now</span>
                            </div>
                            <div class="message-text">
                                <p>Hello! I'm REAgent, your intelligent real estate assistant. I'm here to help you find the perfect home through natural conversation.</p>
                                <p>Just tell me what you're looking for - location, budget, property type, or any specific requirements. I'll learn your preferences and find properties that match exactly what you need.</p>
                                <div class="quick-starters">
                                    <p><strong>Try saying something like:</strong></p>
                                    <div class="starter-buttons">
                                        <button class="starter-btn">"I'm looking for a 2-bedroom flat in London under £500k"</button>
                                        <button class="starter-btn">"Find me a family house with a garden in Manchester"</button>
                                        <button class="starter-btn">"I need a modern apartment near good transport links"</button>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                `;
                
                // Clear recommendations and preferences
                this.updateRecommendations([]);
                this.updatePreferencesDisplay({});
                
                // Generate new session ID
                localStorage.removeItem('reagent_session_id');
                this.sessionId = this.getOrCreateSessionId();
                
            } else {
                throw new Error('Failed to clear session');
            }
            
        } catch (error) {
            console.error('Error clearing chat:', error);
            alert('Failed to clear chat. Please try again.');
        }
    }
}

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.reagentApp = new REAgentApp();
});

// Add some additional CSS for insights modal
const additionalCSS = `
.insights-summary {
    margin-bottom: 2rem;
    padding: 1rem;
    background: var(--bg-secondary);
    border-radius: var(--border-radius);
}

.insights-stats {
    margin-bottom: 2rem;
}

.stat-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
    gap: 1rem;
}

.stat-item {
    text-align: center;
    padding: 1rem;
    background: var(--bg-secondary);
    border-radius: var(--border-radius);
}

.stat-number {
    font-size: 2rem;
    font-weight: 700;
    color: var(--primary-color);
}

.stat-label {
    font-size: 0.875rem;
    color: var(--text-secondary);
    margin-top: 0.25rem;
}

.category-item {
    display: flex;
    justify-content: space-between;
    padding: 0.5rem 0;
    border-bottom: 1px solid var(--border-color);
}

.category-item:last-child {
    border-bottom: none;
}

.category-count {
    font-weight: 600;
    color: var(--primary-color);
}

.property-detail-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 1.5rem;
    gap: 1rem;
}

.property-price-large {
    font-size: 1.5rem;
    font-weight: 700;
    color: var(--primary-color);
}

.detail-row {
    display: flex;
    justify-content: space-between;
    padding: 0.5rem 0;
    border-bottom: 1px solid var(--border-color);
}

.detail-row:last-child {
    border-bottom: none;
}

.detail-label {
    font-weight: 600;
    color: var(--text-secondary);
}

.property-description {
    margin: 1.5rem 0;
    padding: 1rem;
    background: var(--bg-secondary);
    border-radius: var(--border-radius);
}

.property-analysis {
    margin: 1.5rem 0;
}

.pros-section, .cons-section {
    margin-bottom: 1rem;
}

.pros-section h4 {
    color: var(--success-color);
    margin-bottom: 0.5rem;
}

.cons-section h4 {
    color: var(--warning-color);
    margin-bottom: 0.5rem;
}

.pros-section ul, .cons-section ul {
    margin-left: 1rem;
}

.property-actions {
    margin-top: 1.5rem;
    padding-top: 1.5rem;
    border-top: 1px solid var(--border-color);
}
`;

// Add the additional CSS to the page
const style = document.createElement('style');
style.textContent = additionalCSS;
document.head.appendChild(style); 