import { useState, useRef, useEffect } from 'react';
import './App.css';

function App() {
  const [messages, setMessages] = useState([
    {
      id: 1,
      type: 'bot',
      text: 'Assalam o Alaikum! 👋',
      subtext: 'Welcome to Meezan Bank. How may I assist you today?',
      sources: [],
    },
  ]);

  const [inputValue, setInputValue] = useState('');
  const [loading, setLoading] = useState(false);
  const [topK, setTopK] = useState(5);

  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    setTimeout(() => {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, 100);
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSendMessage = async () => {
    if (!inputValue.trim() || loading) return;

    const userMessage = {
      id: Date.now(),
      type: 'user',
      text: inputValue.trim(),
      sources: [],
    };

    setMessages((prev) => [...prev, userMessage]);
    const queryText = inputValue.trim();
    setInputValue('');
    setLoading(true);

    try {
      const response = await fetch('http://localhost:8000/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: queryText,
          use_correction: true,
          top_k: topK,
        }),
      });

      if (!response.ok) throw new Error(`Server error: ${response.status}`);

      const data = await response.json();

      const botMessage = {
        id: Date.now() + 1,
        type: 'bot',
        text: data.answer || "I'm sorry, I couldn't generate a response at this moment.",
        sources: data.context || [],
      };

      setMessages((prev) => [...prev, botMessage]);
    } catch (error) {
      console.error('Error:', error);
      setMessages((prev) => [
        ...prev,
        {
          id: Date.now() + 1,
          type: 'bot',
          text: '❌ Unable to connect to the AI service. Please ensure the backend is running.',
          sources: [],
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <div className="app-container">
      <div className="chat-window">
        {/* Header */}
        <header className="chat-header">
          <div className="header-left">
            <div className="bank-logo">🏦</div>
            <div className="header-title">
              <h1>Meezan Bank</h1>
              <p>Islamic Banking • AI Assistant</p>
            </div>
          </div>

          <div className="header-right">
            <div className="status-indicator">
              <span className="status-dot"></span>
              AI Service Online
            </div>

            <div className="topk-control">
              <label>Relevance Level:</label>
              <select 
                value={topK} 
                onChange={(e) => setTopK(parseInt(e.target.value))}
              >
                <option value={3}>Top 3</option>
                <option value={5}>Top 5</option>
                <option value={7}>Top 7</option>
              </select>
            </div>
          </div>
        </header>

        {/* Messages Area */}
        <div className="messages-container">
          {messages.map((msg) => (
            <div key={msg.id} className={`message-wrapper ${msg.type}`}>
              <div className={`message ${msg.type}`}>
                <p className="message-text">{msg.text}</p>
                {msg.subtext && <p className="message-subtext">{msg.subtext}</p>}

                {msg.sources && msg.sources.length > 0 && (
                  <div className="sources-section">
                    <details>
                      <summary>📚 View Sources ({msg.sources.length})</summary>
                      <div className="sources-list">
                        {msg.sources.map((source, idx) => (
                          <div key={idx} className="source-item">
                            <a
                              href={source.metadata?.metadata?.source_url || '#'}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="source-link"
                            >
                              {source.metadata?.metadata?.source_title || `Document ${idx + 1}`}
                            </a>
                            <span className="source-score">
                              Relevance: {(source.score * 100).toFixed(1)}%
                            </span>
                          </div>
                        ))}
                      </div>
                    </details>
                  </div>
                )}
              </div>
            </div>
          ))}

          {loading && (
            <div className="message-wrapper bot">
              <div className="message bot loading">
                <div className="typing-indicator">
                  <span></span>
                  <span></span>
                  <span></span>
                </div>
                <span className="thinking-text">Thinking...</span>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Footer Input */}
        <div className="chat-footer">
          <div className="input-container">
            <textarea
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask anything about Meezan Bank products, financing, cards, or Shariah compliance..."
              rows={1}
              disabled={loading}
            />
            <button
              onClick={handleSendMessage}
              disabled={loading || !inputValue.trim()}
              className="send-button"
            >
              {loading ? '⏳' : '↑'}
            </button>
          </div>
          <p className="footer-text">
            Meezan Bank • Your Trusted Islamic Banking Partner
          </p>
        </div>
      </div>
    </div>
  );
}

export default App;