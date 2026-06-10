import { useState } from 'react';
import { useChatStore } from '../../stores/chatStore';

export const ChatPanel = () => {
  const { messages, sendMessage } = useChatStore();
  const [input, setInput] = useState('');

  const handleSend = () => {
    if (input.trim()) {
      sendMessage(input);
      setInput('');
    }
  };

  return (
    <div className="flex flex-col h-full bg-slate-900 border-r border-slate-800">
      <div className="flex-1 p-4 overflow-y-auto space-y-4">
        {messages.map(msg => (
          <div key={msg.id} className={`p-3 rounded-lg max-w-[80%] ${msg.role === 'user' ? 'bg-accent-blue ml-auto' : 'bg-slate-800'}`}>
            {msg.content}
          </div>
        ))}
      </div>
      <div className="p-4 border-t border-slate-800 flex gap-2">
        <input 
          type="text" 
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSend()}
          className="flex-1 bg-slate-800 rounded px-4 py-2 outline-none focus:ring-1 focus:ring-accent-blue"
          placeholder="Ask QuantAgent..."
        />
        <button onClick={handleSend} className="bg-accent-blue px-4 py-2 rounded font-semibold">Send</button>
      </div>
    </div>
  );
};
