import { useState, useRef, useEffect } from 'react';

export default function ResidentBot() {
  const [isOpen, setIsOpen] = useState(false);
  
  const [messages, setMessages] = useState(() => {
    const savedChat = sessionStorage.getItem('heimdall_chat_history');
    return savedChat ? JSON.parse(savedChat) : [
      { id: 1, sender: 'bot', text: 'Welcome to Heimdall Assistance. How can I help you navigate the estate or amenities today?' }
    ];
  });
  
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const chatEndRef = useRef(null);
  const backendUrl = import.meta.env.VITE_RAG_BACKEND_URL || "http://localhost:8001";

  useEffect(() => {
    sessionStorage.setItem('heimdall_chat_history', JSON.stringify(messages));
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isTyping]);

  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (!input.trim()) return;

    const userMsg = { id: Date.now(), sender: 'user', text: input };
    setMessages(prev => [...prev, userMsg]);
    
    const currentQuery = input;
    setInput('');
    setIsTyping(true);

    try {
      const response = await fetch(`${backendUrl}/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          question: currentQuery
        })
      });

      if (!response.ok) {
        throw new Error("Failed to fetch");
      }

      const data = await response.json();

      setMessages(prev => [
        ...prev,
        {
          id: Date.now(),
          sender: "bot",
          text: data.answer || data.response || data.result || "Reply received, but JSON key name mismatched."
        }
      ]);

    } catch (err) {
      console.error("AI Connection Error:", err);
      setMessages(prev => [
        ...prev,
        {
          id: Date.now(),
          sender: "bot",
          text: "Unable to contact Heimdall AI."
        }
      ]);
    } finally {
      setIsTyping(false);
    }
  };

  return (
    <div className="fixed bottom-6 right-6 z-50 font-sans">
      {/* Floating Toggle Button */}
      {!isOpen && (
        <button 
          onClick={() => setIsOpen(true)}
          className="bg-blue-600 hover:bg-blue-700 text-white p-4 rounded-full shadow-2xl transition duration-300 border border-blue-500 hover:scale-105"
        >
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
          </svg>
        </button>
      )}

      {/* Chat Window Box */}
      {isOpen && (
        <div className="w-80 sm:w-96 h-[450px] bg-gray-900 border border-gray-800 rounded-2xl shadow-2xl flex flex-col overflow-hidden animate-fadeIn">
          {/* Header */}
          <div className="bg-gray-950 p-4 border-b border-gray-800 flex justify-between items-center">
            <div className="flex items-center space-x-2">
              <div className="w-2 h-2 bg-emerald-500 rounded-full animate-pulse"></div>
              <h3 className="text-sm font-bold text-white tracking-wider">HEIMDALL CONCIERGE AI</h3>
            </div>
            <button onClick={() => setIsOpen(false)} className="text-gray-500 hover:text-white transition">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" /></svg>
            </button>
          </div>

          {/* Messages Wrapper */}
          <div className="flex-1 overflow-y-auto p-4 space-y-3 text-xs" style={{ scrollbarWidth: 'thin', scrollbarColor: '#374151 transparent' }}>
            {messages.map((msg) => (
              <div key={msg.id} className={`flex ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}>
                <div className={`max-w-[80%] rounded-xl px-3 py-2.5 leading-relaxed ${msg.sender === 'user' ? 'bg-blue-600 text-white rounded-br-none' : 'bg-gray-950 border border-gray-800 text-gray-300 rounded-bl-none'}`}>
                  {msg.text}
                </div>
              </div>
            ))}
            
            {/* Thinking / Processing Feedback Animation */}
            {isTyping && (
              <div className="flex justify-start animate-pulse">
                <div className="bg-gray-950 border border-gray-800 text-gray-500 rounded-xl rounded-bl-none px-3 py-2 font-mono">
                  Searching knowledge base...
                </div>
              </div>
            )}
            <div ref={chatEndRef} />
          </div>

          {/* Input Submission Footer */}
          <form onSubmit={handleSendMessage} className="p-3 bg-gray-950 border-t border-gray-800 flex gap-2">
            <input 
              type="text" 
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask about guidelines, parkings, amenities..."
              className="flex-1 bg-gray-900 text-white border border-gray-700 px-3 py-2 rounded-xl text-xs focus:outline-none focus:border-blue-500 transition"
            />
            <button type="submit" className="bg-blue-600 hover:bg-blue-700 text-white font-bold px-3 py-2 rounded-xl text-xs transition">
              Send
            </button>
          </form>
        </div>
      )}
    </div>
  );
}