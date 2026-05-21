"use client";

import { useChat } from "@/hooks/useChat";
import ChatMessage from "./ChatMessage";
import ChatInput from "./ChatInput";

type Props = { onGroqCall: (total: number) => void };

export default function ChatPanel({ onGroqCall }: Props) {
  const { messages, input, setInput, loading, send, endRef } =
    useChat(onGroqCall);

  return (
    <div className="panel span-1">
      <p className="panel-title">SRE Assistant</p>
      <div className="chat-log">
        {messages.length === 0 ? (
          <p className="chat-empty">Ask about your infrastructure…</p>
        ) : (
          messages.map((m, i) => <ChatMessage key={i} message={m} />)
        )}
        {loading && (
          <div className="chat-msg ai">
            <div className="msg-label">SRE-AI</div>
            <div className="analysis-loading" style={{ marginTop: 4 }}>
              <span className="dot-anim">
                <span>.</span>
                <span>.</span>
                <span>.</span>
              </span>
            </div>
          </div>
        )}
        <div ref={endRef} />
      </div>
      <ChatInput
        value={input}
        onChange={setInput}
        onSend={send}
        disabled={loading}
      />
    </div>
  );
}
