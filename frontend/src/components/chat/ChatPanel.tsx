import { useState, useRef, useEffect } from 'react';
import { useChatStore } from '../../stores/chatStore';
import { Send, Bot, Sparkles, AlertCircle, ChevronDown, ChevronUp } from 'lucide-react';

export const ChatPanel = () => {
  const { messages, sendMessage, isStreaming } = useChatStore();
  const [input, setInput] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const [showThinkingMap, setShowThinkingMap] = useState<Record<string, boolean>>({});

  const suggestions = [
    { label: "RSI Mean Reversion AAPL", text: "Run a backtest on AAPL using RSI below 30 to buy and RSI above 70 to exit." },
    { label: "SMA Crossover RELIANCE", text: "Backtest a strategy on RELIANCE where SMA 20 crosses above SMA 50 to buy, and exits when it crosses below." },
    { label: "Bollinger Breakout BTC", text: "Run a Bollinger Bands breakout backtest on BTC-USD for the past 5 years." },
    { label: "How to optimize Sharpe?", text: "Analyze the last backtest results and suggest parameter changes to maximize the Sharpe ratio." }
  ];

  // Scroll to bottom on new messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isStreaming]);

  const handleSend = (textToSend = input) => {
    if (textToSend.trim() && !isStreaming) {
      sendMessage(textToSend);
      if (textToSend === input) setInput('');
    }
  };

  const toggleThinking = (msgId: string) => {
    setShowThinkingMap(prev => ({ ...prev, [msgId]: !prev[msgId] }));
  };

  // Helper to parse DeepSeek-R1 thinking tags
  const parseMessageContent = (content: string) => {
    const thinkRegex = /<think>([\s\S]*?)<\/think>/;
    const match = content.match(thinkRegex);
    
    if (match) {
      const thinking = match[1].trim();
      const mainContent = content.replace(thinkRegex, '').trim();
      return { thinking, mainContent };
    }
    
    return { thinking: null, mainContent: content };
  };

  return (
    <div className="flex flex-col h-full bg-[#0b0f19] border border-slate-800 rounded-xl overflow-hidden shadow-xl text-slate-100">
      
      {/* Header */}
      <div className="px-4 py-3.5 border-b border-slate-800 bg-slate-900/60 backdrop-blur-md flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="h-8 w-8 rounded-lg bg-blue-600/10 border border-blue-500/30 flex items-center justify-center text-blue-400">
            <Bot size={18} />
          </div>
          <div>
            <div className="font-bold text-xs text-slate-100">AI Strategy Assistant</div>
            <div className="text-[9px] text-slate-500 font-mono">DeepSeek-R1 Model Active</div>
          </div>
        </div>
        <span className="flex h-2 w-2 relative">
          <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
          <span className="relative inline-flex rounded-full h-2 w-2 bg-green-500"></span>
        </span>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-slate-950/20 scrollbar-thin scrollbar-thumb-slate-800">
        {messages.length === 0 ? (
          <div className="h-full flex flex-col justify-center items-center text-center p-6 space-y-6">
            <div className="h-12 w-12 rounded-full bg-blue-600/5 border border-blue-500/20 flex items-center justify-center text-blue-500/60">
              <Bot size={28} />
            </div>
            <div>
              <h4 className="font-bold text-sm text-slate-300">Interact Directly with AI Backtester</h4>
              <p className="text-xs text-slate-500 mt-1.5 max-w-xs leading-relaxed">
                Describe a strategy in plain English, and the assistant will convert it to rules, execute the backtest, and display the charts!
              </p>
            </div>
            
            {/* Quick Actions suggestions */}
            <div className="w-full space-y-2 text-left">
              <div className="text-[9px] font-bold uppercase text-slate-600 tracking-wider mb-2 flex items-center gap-1">
                <Sparkles size={10} /> Suggested Operations
              </div>
              {suggestions.map((s, i) => (
                <button
                  key={i}
                  onClick={() => handleSend(s.text)}
                  className="w-full text-left bg-slate-900/50 hover:bg-[#11192e] border border-slate-800/80 hover:border-slate-700/60 p-2.5 rounded-lg text-[11px] text-slate-300 transition-all cursor-pointer"
                >
                  {s.label}
                </button>
              ))}
            </div>
          </div>
        ) : (
          messages.map((msg) => {
            const isUser = msg.role === 'user';
            const { thinking, mainContent } = parseMessageContent(msg.content);
            const isThinkingOpen = showThinkingMap[msg.id] ?? false;

            return (
              <div key={msg.id} className={`flex flex-col ${isUser ? 'items-end' : 'items-start'}`}>
                {/* Message Bubble */}
                <div
                  className={`max-w-[90%] px-3.5 py-2.5 rounded-xl text-xs leading-relaxed shadow-sm ${
                    isUser
                      ? 'bg-blue-600 text-white rounded-br-none'
                      : 'bg-slate-900 border border-slate-800 text-slate-200 rounded-bl-none'
                  }`}
                >
                  {/* Thinking Section */}
                  {thinking && !isUser && (
                    <div className="mb-3 border-b border-slate-800/80 pb-2">
                      <button
                        onClick={() => toggleThinking(msg.id)}
                        className="flex items-center gap-1 text-[9px] text-slate-400 font-bold uppercase tracking-wider hover:text-slate-200 cursor-pointer"
                      >
                        {isThinkingOpen ? <ChevronUp size={10} /> : <ChevronDown size={10} />}
                        Reasoning Process
                      </button>
                      {isThinkingOpen && (
                        <div className="mt-1.5 font-mono text-[9px] text-slate-500 bg-slate-950 p-2 rounded max-h-[120px] overflow-y-auto whitespace-pre-wrap leading-normal border border-slate-950">
                          {thinking}
                        </div>
                      )}
                    </div>
                  )}

                  {/* Main Text Content */}
                  <div className="whitespace-pre-wrap text-slate-200 font-sans leading-relaxed">
                    {mainContent}
                  </div>
                </div>
              </div>
            );
          })
        )}
        
        {isStreaming && (
          <div className="flex items-center gap-2 text-slate-400 text-xs bg-slate-900/40 p-3 rounded-lg border border-slate-800/60 max-w-[150px]">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-blue-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-blue-500"></span>
            </span>
            <span className="font-mono text-[10px]">Thinking...</span>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Form */}
      <div className="p-3 border-t border-slate-800/80 bg-slate-900/40 backdrop-blur-md">
        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSend()}
            placeholder="Type strategy rules or questions..."
            disabled={isStreaming}
            className="flex-1 bg-slate-950 border border-slate-850 rounded-lg pl-3 pr-3 py-2 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 disabled:opacity-50"
          />
          <button
            onClick={() => handleSend()}
            disabled={isStreaming || !input.trim()}
            className="bg-blue-600 hover:bg-blue-700 disabled:bg-slate-800 disabled:text-slate-500 text-white p-2 rounded-lg transition-all flex items-center justify-center cursor-pointer disabled:cursor-not-allowed"
          >
            <Send size={14} />
          </button>
        </div>
        <div className="flex items-center gap-1 text-[9px] text-slate-500 mt-2 px-1">
          <AlertCircle size={10} />
          <span>Formulates strategy JSON parameters dynamically.</span>
        </div>
      </div>
    </div>
  );
};
