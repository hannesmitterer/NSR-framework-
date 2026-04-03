import React, { useMemo } from 'react';

const NODES = [
  { id: 'RADICE',   x: 200, y: 120, color: '#3fb950', emoji: '🌱' },
  { id: 'SILENZIO', x: 400, y: 250, color: '#58a6ff', emoji: '🔵' },
  { id: 'NODO',     x: 200, y: 380, color: '#d29922', emoji: '⚡' },
  { id: 'HUB',      x: 400, y: 120, color: '#8b949e', emoji: '🌐' },
];

function scoreToRadius(score) {
  return 24 + (score || 0.5) * 20;
}

export default function NetworkGraph({ reputation, messages }) {
  const lastActivity = useMemo(() => {
    const map = {};
    (messages || []).forEach(m => {
      if (m.role) map[m.role] = m.timestamp;
    });
    return map;
  }, [messages]);

  const now = Date.now() / 1000;

  return (
    <div style={{
      background: 'var(--surface)', border: '1px solid var(--border)',
      borderRadius: 'var(--radius)', overflow: 'hidden',
    }}>
      <div style={{
        padding: '12px 16px', fontSize: '0.85rem', fontWeight: 600,
        color: 'var(--muted)', textTransform: 'uppercase', letterSpacing: '0.05em',
        borderBottom: '1px solid var(--border)',
      }}>
        🕸 Network Topology
      </div>
      <div style={{ padding: '14px 16px' }}>
        <svg width="100%" viewBox="0 0 600 500" style={{ maxHeight: 280 }}>
          {/* Edges hub ↔ agents */}
          {NODES.filter(n => n.id !== 'HUB').map(n => (
            <line key={n.id}
              x1={400} y1={120} x2={n.x} y2={n.y}
              stroke="var(--border)" strokeWidth={1.5} strokeDasharray="4 3"
            />
          ))}

          {/* Nodes */}
          {NODES.map(n => {
            const score = reputation[n.id] ?? (n.id === 'HUB' ? 1 : 0.5);
            const r = scoreToRadius(score);
            const recent = lastActivity[n.id] && (now - lastActivity[n.id]) < 10;
            return (
              <g key={n.id}>
                {recent && (
                  <circle cx={n.x} cy={n.y} r={r + 8}
                    fill="none" stroke={n.color} strokeWidth={1.5} opacity={0.4}>
                    <animate attributeName="r" from={r} to={r + 14}
                      dur="1.5s" repeatCount="indefinite" />
                    <animate attributeName="opacity" from={0.4} to={0}
                      dur="1.5s" repeatCount="indefinite" />
                  </circle>
                )}
                <circle cx={n.x} cy={n.y} r={r} fill={n.color} opacity={0.15} />
                <circle cx={n.x} cy={n.y} r={r * 0.6} fill={n.color} opacity={0.7} />
                <text x={n.x} y={n.y + 5} textAnchor="middle"
                  fontSize={14} fill="white">{n.emoji}</text>
                <text x={n.x} y={n.y + r + 16} textAnchor="middle"
                  fontSize={12} fill="var(--text)" fontWeight={600}>{n.id}</text>
                <text x={n.x} y={n.y + r + 30} textAnchor="middle"
                  fontSize={10} fill="var(--muted)">
                  {score.toFixed(2)}
                </text>
              </g>
            );
          })}
        </svg>
      </div>
    </div>
  );
}
