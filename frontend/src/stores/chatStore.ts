import { create } from 'zustand'
import type { Message } from '../types'
import { sendChatMessage } from '../services/api'

interface ChatState {
  messages: Message[];
  isStreaming: boolean;
  sessionId: string;
  sendMessage: (msg: string) => Promise<void>;
  appendToken: (token: string) => void;
}

export const useChatStore = create<ChatState>((set, get) => ({
  messages: [],
  isStreaming: false,
  sessionId: crypto.randomUUID(),
  sendMessage: async (msg) => {
    set((state) => ({
      messages: [...state.messages, { id: crypto.randomUUID(), role: 'user', content: msg, timestamp: Date.now() }]
    }))

    try {
      const { response } = await sendChatMessage(msg, get().sessionId)
      set((state) => ({
        messages: [...state.messages, { id: crypto.randomUUID(), role: 'agent', content: response, timestamp: Date.now() }]
      }))
    } catch (error) {
      set((state) => ({
        messages: [...state.messages, { id: crypto.randomUUID(), role: 'agent', content: `Error: ${String(error)}`, timestamp: Date.now() }]
      }))
    }
  },
  appendToken: (_token) => set((state) => {
    return state;
  })
}))
