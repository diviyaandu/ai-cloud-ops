type Props = {
  value: string;
  onChange: (v: string) => void;
  onSend: () => void;
  disabled: boolean;
};

export default function ChatInput({
  value,
  onChange,
  onSend,
  disabled,
}: Props) {
  return (
    <div className="chat-input-row">
      <input
        className="chat-input"
        placeholder="e.g. why is CPU spiking?"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        onKeyDown={(e) => e.key === "Enter" && onSend()}
      />
      <button className="chat-send" onClick={onSend} disabled={disabled}>
        SEND
      </button>
    </div>
  );
}
