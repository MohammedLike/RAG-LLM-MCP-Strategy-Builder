import { useState, useRef, useEffect } from 'react';
import { useChatStore } from '../../stores/chatStore';
import { Send, Bot, Sparkles, AlertCircle } from 'lucide-react';

export const ChatPanel = () => {
  const { messages, sendMessage, isStreaming } = useChatStore();
  const [input, setInput] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isStreaming]);

  const handleSend = (textToSend = input) => {
    if (textToSend.trim() && !isStreaming) {
      sendMessage(textToSend);
      if (textToSend === input) setInput('');
    }
  };

  const suggestions = [
    "Backtest NIFTY RSI < 30, exit RSI > 70, 2y",
    "SMA 20 crosses above SMA 50 on RELIANCE",
    "Backtest BANKNIFTY ATM Straddle, 1y",
  ];

  const renderMessageContent = (content: string) => {
    // Check for standard <think> tags
    const thinkRegex = /<think>([\s\S]*?)<\/think>/i;
    const match = content.match(thinkRegex);
    
    if (match) {
      const thinking = match[1].trim();
      const actualResponse = content.replace(thinkRegex, '').trim();
      
      return (
        <div className="space-y-2">
          <details className="group border border-slate-800/80 bg-slate-950/40 rounded p-1.5 transition">
            <summary className="text-[8px] font-bold text-slate-500 uppercase tracking-wider cursor-pointer list-none flex items-center justify-between group-open:mb-1.5 select-none">
              <span className="flex items-center gap-1">
                <span className="h-1 w-1 rounded-full bg-slate-500 animate-pulse"></span>
                Thinking Process
              </span>
              <span className="text-[7px] text-slate-600 font-mono transition-transform duration-200 group-open:rotate-180">▼</span>
            </summary>
            <div className="text-[8.5px] text-slate-500 font-mono leading-relaxed border-t border-slate-800/40 pt-1.5 whitespace-pre-wrap select-text">
              {thinking}
            </div>
          </details>
          {actualResponse && (
            <div className="whitespace-pre-wrap select-text">{actualResponse}</div>
          )}
        </div>
      );
    }

    // Support the weird <｜end▁of▁thinking｜> tag structure if present
    const splitTag = '<｜end▁of▁thinking｜>';
    if (content.includes(splitTag)) {
      const parts = content.split(splitTag);
      const thinking = parts[0].replace(/<｜begin▁of▁thinking｜>/g, '').trim();
      const actualResponse = parts.slice(1).join(splitTag).trim();
      
      return (
        <div className="space-y-2">
          <details className="group border border-slate-800/80 bg-slate-950/40 rounded p-1.5 transition">
            <summary className="text-[8px] font-bold text-slate-500 uppercase tracking-wider cursor-pointer list-none flex items-center justify-between group-open:mb-1.5 select-none">
              <span className="flex items-center gap-1">
                <span className="h-1 w-1 rounded-full bg-slate-500 animate-pulse"></span>
                Thinking Process
              </span>
              <span className="text-[7px] text-slate-600 font-mono transition-transform duration-200 group-open:rotate-180">▼</span>
            </summary>
            <div className="text-[8.5px] text-slate-500 font-mono leading-relaxed border-t border-slate-800/40 pt-1.5 whitespace-pre-wrap select-text">
              {thinking}
            </div>
          </details>
          {actualResponse && (
            <div className="whitespace-pre-wrap select-text">{actualResponse}</div>
          )}
        </div>
      );
    }
    
    return <div className="whitespace-pre-wrap select-text">{content}</div>;
  };

  return (
    <div className="flex flex-col h-full bg-[#0a0e17] text-slate-100">
      <div className="px-3 py-2.5 border-b border-slate-800/80 bg-slate-900/40 flex items-center justify-between shrink-0">
        <div className="flex items-center gap-2">
          <div className="h-6 w-6 rounded bg-[#00d09c]/10 border border-[#00d09c]/20 flex items-center justify-center text-[#00d09c]">
            <Bot size={12} />
          </div>
          <div>
            <div className="font-black text-[10px] text-white uppercase tracking-tight">STREAK <span className="text-[#00d09c]">AI</span></div>
            <div className="text-[7px] text-slate-500 font-bold uppercase tracking-widest">QUANT ASSISTANT</div>
          </div>
        </div>
        <span className="flex h-1.5 w-1.5 relative">
          <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#00d09c] opacity-40"></span>
          <span className="relative inline-flex rounded-full h-1.5 w-1.5 bg-[#00d09c]"></span>
        </span>
      </div>
 
      <div className="flex-1 overflow-y-auto px-3 py-3 space-y-3 text-[10px] bg-slate-950/10">
        {messages.length === 0 ? (
          <div className="h-full flex flex-col justify-center items-center text-center px-2 space-y-4">
            <div className="h-10 w-10 rounded-2xl bg-[#00d09c]/5 border border-[#00d09c]/10 flex items-center justify-center text-[#00d09c]/40">
              <Sparkles size={20} />
            </div>
            <div>
              <h4 className="font-black text-[11px] text-slate-300 uppercase tracking-tight">NLP QUANT ENGINE</h4>
              <p className="text-[9px] text-slate-500 mt-1 leading-relaxed">Describe a strategy in plain English and I'll backtest it.</p>
            </div>
            <div className="w-full space-y-1.5">
              <div className="text-[7px] font-black uppercase text-slate-600 tracking-widest mb-2">Try saying:</div>
              {suggestions.map((s, i) => (
                <button key={i} onClick={() => handleSend(s)}
                  className="w-full text-left bg-slate-900/30 hover:bg-slate-800/50 border border-slate-800/80 p-2 rounded text-[9px] text-slate-400 font-bold transition cursor-pointer">
                  {s}
                </button>
              ))}
            </div>
          </div>
        ) : (
          messages.map((msg) => (
            <div key={msg.id} className={`flex flex-col ${msg.role === 'user' ? 'items-end' : 'items-start'}`}>
              <div className={`max-w-[95%] px-2.5 py-2 rounded text-[10px] leading-relaxed ${
                msg.role === 'user'
                  ? 'bg-[#00d09c] text-[#06090f] font-bold rounded-tr-none'
                  : 'bg-slate-900 border border-slate-800 text-slate-200 rounded-tl-none'
              }`}>
                {msg.role === 'user' ? (
                  <div className="whitespace-pre-wrap select-text">{msg.content}</div>
                ) : (
                  renderMessageContent(msg.content)
                )}
              </div>
            </div>
          ))
        )}
        {isStreaming && (
          <div className="flex items-center gap-2 text-slate-500 bg-slate-900/50 p-2 rounded border border-slate-800/80 max-w-[120px]">
            <div className="flex gap-0.5"><span className="h-1 w-1 bg-[#00d09c] rounded-full animate-bounce" style={{animationDelay:'0s'}}></span>
              <span className="h-1 w-1 bg-[#00d09c] rounded-full animate-bounce" style={{animationDelay:'0.2s'}}></span>
              <span className="h-1 w-1 bg-[#00d09c] rounded-full animate-bounce" style={{animationDelay:'0.4s'}}></span></div>
            <span className="font-black text-[8px] uppercase tracking-widest">Thinking...</span>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <div className="p-3 border-t border-slate-800/80 bg-slate-900/40 shrink-0">
        <div className="flex gap-1.5">
          <input type="text" value={input} onChange={e => setInput(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && handleSend()}
            placeholder="Describe your strategy..." disabled={isStreaming}
            className="flex-1 bg-slate-950 border border-slate-800 rounded px-2.5 py-1.5 text-[10px] text-white placeholder-slate-600 focus:outline-none focus:border-[#00d09c]/50 disabled:opacity-50 font-medium" />
          <button onClick={() => handleSend()} disabled={isStreaming || !input.trim()}
            className="bg-[#00d09c] hover:bg-[#00b386] disabled:bg-slate-800 disabled:text-slate-600 text-[#06090f] p-1.5 rounded transition cursor-pointer disabled:cursor-not-allowed">
            <Send size={12} />
          </button>
        </div>
        <div className="flex items-center gap-1 text-[7px] text-slate-600 mt-1.5 font-bold uppercase tracking-tighter px-0.5">
          <AlertCircle size={8} />
          <span>Vectorized simulation based on NLP input</span>
        </div>
      </div>
    </div>
  );
};
