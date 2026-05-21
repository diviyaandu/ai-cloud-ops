"use client";

import { useEffect, useRef, useState } from "react";
import { sendChatMessage } from "@/services/api";
import type { ChatMessage } from "@/types/metrics";

export function useChat(onGroqCall: (total: number) => void) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const send = async () => {
    const msg = input.trim();
    if (!msg || loading) return;
    setInput("");
    setMessages((prev) => [...prev, { role: "user", text: msg }]);
    setLoading(true);
    try {
      const data = await sendChatMessage(msg, messages);
      onGroqCall(data.groq_calls_total);
      setMessages((prev) => [
        ...prev,
        { role: "ai", text: data.response || "No response." },
      ]);
    } catch (e: any) {
      setMessages((prev) => [
        ...prev,
        { role: "ai", text: `Error: ${e.message}` },
      ]);
    }
    setLoading(false);
  };

  return { messages, input, setInput, loading, send, endRef };
}
