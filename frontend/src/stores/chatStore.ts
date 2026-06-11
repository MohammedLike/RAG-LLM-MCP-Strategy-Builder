import { create } from 'zustand'
import type { Message } from '../types'
import { sendChatMessage } from '../services/api'
import { useBacktestStore } from './backtestStore'

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
      messages: [...state.messages, { id: crypto.randomUUID(), role: 'user', content: msg, timestamp: Date.now() }],
      isStreaming: true,
    }))

    try {
      const data = await sendChatMessage(msg, get().sessionId)
      const content = data.response ?? data.error ?? 'No response'
      set((state) => ({
        messages: [...state.messages, { id: crypto.randomUUID(), role: 'agent', content, timestamp: Date.now() }],
        isStreaming: false,
      }))
      
      // Refresh backtest data from the backend in case the agent ran a backtest
      await useBacktestStore.getState().fetchLatestBacktest();
    } catch (error) {
      set((state) => ({
        messages: [...state.messages, { id: crypto.randomUUID(), role: 'agent', content: `Error: ${String(error)}`, timestamp: Date.now() }],
        isStreaming: false,
      }))
    }
  },
  appendToken: (_token) => set((state) => {
    return state;
  })
}))

