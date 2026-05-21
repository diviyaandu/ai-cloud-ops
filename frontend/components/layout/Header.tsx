"use client";

type Props = {
  health: string;
  healthColor: string;
  tick: number;
  groqCalls: number;
};

export default function Header({
  health,
  healthColor,
  tick,
  groqCalls,
}: Props) {
  return (
    <header className="header">
      <div>
        <h1 className="header-title">AI Cloud Ops</h1>
        <p className="header-sub">Infrastructure Intelligence Dashboard</p>
      </div>
      <div className="header-right">
        <div
          className="health-pill"
          style={{
            color: healthColor,
            borderColor: `${healthColor}44`,
            background: `${healthColor}12`,
          }}
        >
          <span className="health-dot" style={{ background: healthColor }} />
          {health}
        </div>
        <span className="tick-counter">
          POLL #{tick} · every 3s &nbsp;·&nbsp; GROQ CALLS: {groqCalls}
        </span>
      </div>
    </header>
  );
}
