import React from 'react';

const ROLE_COLORS = {
  RADICE: 'var(--green)',
  SILENZIO: 'var(--accent)',
  NODO: 'var(--yellow)',
  external: 'var(--muted)',
};

function ts(unix) {
  return unix ? new Date(unix * 1000).toLocaleTimeString() : '';
}

function MessageItem({ msg }) {
  const role = msg.role || 'external';
  const text = msg.contribution || msg.data || JSON.stringify(msg);
  const color = ROLE_COLORS[role] || 'var(--muted)';
  return (
    <div style={{
      background: 'var(--bg)', border: '1px solid var(--border)',
      borderRadius: 6, padding: '8px 12px', fontSize: '0.8rem',
    }}>
      <div style={{ fontWeight: 700, color, marginBottom: 4 }}>{role}</div>
      <div style={{ color: 'var(--muted)', wordBreak: 'break-word' }}>
        {String(text).slice(0, 400)}
      </div>
      <div style={{ color: 'var(--border)', fontSize: '0.7rem', marginTop: 4 }}>
        {ts(msg.timestamp)} {msg.node_id ? `· node ${msg.node_id}` : ''}
        {msg.cycle ? ` · cycle ${msg.cycle}` : ''}
      </div>
    </div>
  );
}

export default function MessageFeed({ messages }) {
  return (
    <div style={{
      background: 'var(--surface)', border: '1px solid var(--border)',
      borderRadius: 'var(--radius)', overflow: 'hidden',
    }}>
      <div style={{
        padding: '12px 16px', fontSize: '0.85rem', fontWeight: 600,
        color: 'var(--muted)', textTransform: 'uppercase', letterSpacing: '0.05em',
        borderBottom: '1px solid var(--border)',
        display: 'flex', justifyContent: 'space-between', alignItems: 'center',
      }}>
        <span>📡 Live Messages</span>
        <span style={{ fontSize: '0.75rem' }}>{messages.length} total</span>
      </div>
      <div style={{
        padding: '14px 16px', maxHeight: 360, overflowY: 'auto',
        display: 'flex', flexDirection: 'column', gap: 6,
      }}>
        {messages.length === 0
          ? <p style={{ color: 'var(--muted)', fontSize: '0.82rem' }}>No messages yet.</p>
          : messages.slice(0, 50).map((m, i) => <MessageItem key={i} msg={m} />)
        }
      </div>
    </div>
  );
}
