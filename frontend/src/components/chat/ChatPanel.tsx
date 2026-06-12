import { useState, useRef, useEffect } from 'react';
import { useChatStore } from '../../stores/chatStore';
import { Send, Bot, Sparkles, AlertCircle, ChevronDown, ChevronUp } from 'lucide-react';

export const ChatPanel = () => {
  const { messages, sendMessage, isStreaming } = useChatStore();
  const [input, setInput] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const [showThinkingMap, setShowThinkingMap] = useState<Record<string, boolean>>({});

  const suggestions = [
    { label: "RSI Bullish NIFTY 50", text: "Backtest NIFTY when RSI crosses above 40 and exit at 1% target profit." },
    { label: "SMA Crossover RELIANCE", text: "Backtest RELIANCE where SMA 20 crosses above SMA 50. Use 2% stop loss." },
    { label: "Supertrend BANKNIFTY", text: "Run a backtest on BANKNIFTY using Supertrend (7, 3) signals for the past 2 years." },
    { label: "Optimization Advice", text: "Analyze the last backtest results and suggest parameter changes to maximize the Win Rate." }
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
    <div className="flex flex-col h-full bg-[#0a0e17] text-slate-100">
      
      {/* Header */}
      <div className="px-5 py-4 border-b border-slate-800/80 bg-slate-900/40 backdrop-blur-md flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="h-9 w-9 rounded bg-[#00d09c]/10 border border-[#00d09c]/20 flex items-center justify-center text-[#00d09c]">
            <Bot size={20} />
          </div>
          <div>
            <div className="font-black text-xs text-white uppercase tracking-tight">STREAK <span className="text-[#00d09c]">AI</span> ASSISTANT</div>
            <div className="text-[9px] text-slate-500 font-bold uppercase tracking-widest">PRO SIMULATOR ACTIVE</div>
          </div>
        </div>
        <span className="flex h-2 w-2 relative">
          <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#00d09c] opacity-40"></span>
          <span className="relative inline-flex rounded-full h-2 w-2 bg-[#00d09c]"></span>
        </span>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-5 space-y-6 bg-slate-950/10 scrollbar-thin scrollbar-thumb-slate-800">
        {messages.length === 0 ? (
          <div className="h-full flex flex-col justify-center items-center text-center p-6 space-y-8">
            <div className="h-16 w-16 rounded-3xl bg-[#00d09c]/5 border border-[#00d09c]/10 flex items-center justify-center text-[#00d09c]/40">
              <Sparkles size={32} />
            </div>
            <div>
              <h4 className="font-black text-sm text-slate-200 uppercase tracking-tight">NLP QUANT ENGINE</h4>
              <p className="text-xs text-slate-500 mt-2 max-w-[240px] leading-relaxed font-medium">
                Describe any Indian market strategy in plain English. I'll transform it into vectors and simulate performance instantly.
              </p>
            </div>
            
            {/* Quick Actions suggestions */}
            <div className="w-full space-y-2.5 text-left">
              <div className="text-[9px] font-black uppercase text-slate-600 tracking-widest mb-3 flex items-center gap-2">
                <div className="h-px flex-1 bg-slate-800/80"></div>
                Suggested Prompts
                <div className="h-px flex-1 bg-slate-800/80"></div>
              </div>
              {suggestions.map((s, i) => (
                <button
                  key={i}
                  onClick={() => handleSend(s.text)}
                  className="w-full text-left bg-slate-900/30 hover:bg-slate-800/50 border border-slate-800/80 hover:border-[#00d09c]/30 p-3 rounded-lg text-[11px] text-slate-400 font-bold transition-all cursor-pointer group"
                >
                  <span className="text-[#00d09c]/60 group-hover:text-[#00d09c] transition-colors mr-2">/</span>
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
                  className={`max-w-[92%] px-4 py-3 rounded-lg text-xs leading-relaxed shadow-lg ${
                    isUser
                      ? 'bg-[#00d09c] text-[#06090f] font-bold rounded-tr-none'
                      : 'bg-slate-900 border border-slate-800 text-slate-200 rounded-tl-none'
                  }`}
                >
                  {/* Thinking Section */}
                  {thinking && !isUser && (
                    <div className="mb-4 border-b border-slate-800/80 pb-3">
                      <button
                        onClick={() => toggleThinking(msg.id)}
                        className="flex items-center gap-2 text-[9px] text-[#00d09c] font-black uppercase tracking-widest hover:text-[#00d09c]/80 cursor-pointer"
                      >
                        {isThinkingOpen ? <ChevronUp size={10} /> : <ChevronDown size={10} />}
                        REASONING LOG
                      </button>
                      {isThinkingOpen && (
                        <div className="mt-2.5 font-mono text-[10px] text-slate-500 bg-slate-950 p-3 rounded leading-normal border border-slate-900 overflow-x-auto">
                          {thinking}
                        </div>
                      )}
                    </div>
                  )}

                  {/* Main Text Content */}
                  <div className="whitespace-pre-wrap font-medium leading-relaxed">
                    {mainContent}
                  </div>
                </div>
              </div>
            );
          })
        )}
        
        {isStreaming && (
          <div className="flex items-center gap-3 text-slate-500 bg-slate-900/50 p-3 rounded-lg border border-slate-800/80 max-w-[160px]">
            <div className="flex gap-1">
              <span className="h-1 w-1 bg-[#00d09c] rounded-full animate-bounce" style={{ animationDelay: '0s' }}></span>
              <span className="h-1 w-1 bg-[#00d09c] rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></span>
              <span className="h-1 w-1 bg-[#00d09c] rounded-full animate-bounce" style={{ animationDelay: '0.4s' }}></span>
            </div>
            <span className="font-black text-[9px] uppercase tracking-widest">Simulating...</span>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Form */}
      <div className="p-4 border-t border-slate-800/80 bg-slate-900/40">
        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSend()}
            placeholder="Type strategy (e.g. Backtest SBI RSI > 40)..."
            disabled={isStreaming}
            className="flex-1 bg-slate-950 border border-slate-800 rounded pl-4 pr-4 py-2.5 text-xs text-white placeholder-slate-600 focus:outline-none focus:border-[#00d09c]/50 disabled:opacity-50 font-medium"
          />
          <button
            onClick={() => handleSend()}
            disabled={isStreaming || !input.trim()}
            className="bg-[#00d09c] hover:bg-[#00b386] disabled:bg-slate-800 disabled:text-slate-600 text-[#06090f] p-2.5 rounded transition-all flex items-center justify-center cursor-pointer disabled:cursor-not-allowed shadow-lg"
          >
            <Send size={16} />
          </button>
        </div>
        <div className="flex items-center gap-2 text-[9px] text-slate-600 mt-3 font-bold uppercase tracking-tighter px-1">
          <AlertCircle size={10} />
          <span>Vectorized order execution based on NLP input</span>
        </div>
      </div>
    </div>
  );
};
