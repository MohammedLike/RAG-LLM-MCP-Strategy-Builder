import { create } from 'zustand'
import { Message } from '../types'

interface ChatState {
  messages: Message[];
  isStreaming: boolean;
  sessionId: string;
  sendMessage: (msg: string) => void;
  appendToken: (token: string) => void;
}

export const useChatStore = create<ChatState>((set) => ({
  messages: [],
  isStreaming: false,
  sessionId: crypto.randomUUID(),
  sendMessage: (msg) => set((state) => ({
    messages: [...state.messages, { id: crypto.randomUUID(), role: 'user', content: msg, timestamp: Date.now() }]
  })),
  appendToken: (token) => set((state) => {
    // Basic streaming implementation
    return state;
  })
}))
