import { X, Send, Bot } from 'lucide-react';
import { useState } from 'react';
import { useChatStore } from '../../stores/chatStore';

interface ChatDrawerProps {
  open: boolean;
  onClose: () => void;
}

export const ChatDrawer = ({ open, onClose }: ChatDrawerProps) => {
  const { messages, sendMessage, isStreaming } = useChatStore();
  const [input, setInput] = useState('');

  const handleSend = () => {
    if (input.trim() && !isStreaming) {
      sendMessage(input);
      setInput('');
    }
  };

  if (!open) return null;

  return (
    <>
      <div className="fixed inset-0 bg-black/20 z-40" onClick={onClose} />
      <div className="fixed right-0 top-0 h-full w-full max-w-[420px] bg-white shadow-2xl z-50 flex flex-col border-l border-[#e5e9f0]">
        <div className="flex items-center justify-between px-5 py-4 border-b border-[#e5e9f0] bg-gradient-to-r from-brand to-blue-500 text-white">
          <div className="flex items-center gap-2">
            <Bot size={20} />
            <div>
              <div className="font-bold text-sm">Quant AI Assistant</div>
              <div className="text-[11px] text-white/80">Powered by DeepSeek-R1</div>
            </div>
          </div>
          <button onClick={onClose} className="p-1.5 rounded-lg hover:bg-white/20">
            <X size={18} />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-4 space-y-3 bg-slate-50">
          {messages.length === 0 && (
            <div className="text-center py-12 text-muted">
              <Bot size={40} className="mx-auto mb-3 text-brand opacity-40" />
              <p className="text-sm font-medium text-slate-700">Ask me about strategies, market data, or backtests</p>
              <p className="text-xs mt-1">e.g. &quot;When should I enter a short strangle?&quot;</p>
            </div>
          )}
          {messages.map((msg) => (
            <div
              key={msg.id}
              className={`max-w-[85%] px-3.5 py-2.5 rounded-2xl text-sm leading-relaxed ${
                msg.role === 'user'
                  ? 'ml-auto bg-brand text-white rounded-br-md'
                  : 'bg-white border border-[#e5e9f0] text-slate-800 rounded-bl-md shadow-sm'
              }`}
            >
              {msg.content}
            </div>
          ))}
          {isStreaming && (
            <div className="bg-white border border-[#e5e9f0] px-3.5 py-2.5 rounded-2xl rounded-bl-md text-sm text-muted">
              Thinking...
            </div>
          )}
        </div>

        <div className="p-4 border-t border-[#e5e9f0] bg-white">
          <div className="flex gap-2">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSend()}
              placeholder="Ask about Nifty, BankNifty strategies..."
              className="flex-1 px-4 py-2.5 rounded-xl border border-[#e5e9f0] text-sm outline-none focus:border-brand focus:ring-2 focus:ring-brand/20"
            />
            <button
              onClick={handleSend}
              disabled={isStreaming}
              className="btn-primary px-4 py-2.5 flex items-center gap-1 disabled:opacity-50"
            >
              <Send size={16} />
            </button>
          </div>
        </div>
      </div>
    </>
  );
};
