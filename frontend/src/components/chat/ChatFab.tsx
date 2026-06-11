import { MessageCircle } from 'lucide-react';

interface ChatFabProps {
  onClick: () => void;
}

export const ChatFab = ({ onClick }: ChatFabProps) => (
  <button
    onClick={onClick}
    className="fixed bottom-6 right-6 z-30 flex items-center gap-2 bg-brand hover:bg-brand-dark text-white pl-4 pr-5 py-3 rounded-full shadow-lg shadow-brand/30 transition-all hover:scale-105"
  >
    <MessageCircle size={20} />
    <span className="text-sm font-semibold hidden sm:inline">Need Help? Chat with our AI bot</span>
  </button>
);
