import type { ChatMessage as ChatMessageType } from "@/types/metrics";

type Props = { message: ChatMessageType };

export default function ChatMessage({ message }: Props) {
  const isUser = message.role === "user";
  return (
    <div className={`chat-msg ${message.role}`}>
      <div className="msg-label">{isUser ? "YOU" : "SRE-AI"}</div>
      <div className="msg-text">{message.text}</div>
    </div>
  );
}
