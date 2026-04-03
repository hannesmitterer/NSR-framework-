import React from 'react';

export default function ChainPanel({ chain }) {
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
        ⛓ Immutable Hash Chain
      </div>
      <div style={{ padding: '14px 16px', display: 'flex', flexDirection: 'column', gap: 8 }}>
        <div style={{ fontSize: '0.82rem' }}>
          <span style={{ color: 'var(--muted)' }}>Length: </span>
          <code style={{ color: 'var(--accent)' }}>{chain?.length ?? 0}</code>
        </div>
        <div style={{ fontSize: '0.82rem' }}>
          <span style={{ color: 'var(--muted)' }}>Last hash: </span>
          <code style={{ color: 'var(--accent)', wordBreak: 'break-all', fontSize: '0.75rem' }}>
            {chain?.last_hash ?? 'GENESIS'}
          </code>
        </div>
        <div style={{ fontSize: '0.78rem', color: 'var(--muted)', marginTop: 4 }}>
          Every anchored knowledge block is hashed into a tamper-evident chain.
        </div>
      </div>
    </div>
  );
}
