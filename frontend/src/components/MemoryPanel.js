import React from 'react';

export default function MemoryPanel({ memory }) {
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
        🧠 Shared Memory
      </div>
      <div style={{
        padding: '14px 16px', maxHeight: 260, overflowY: 'auto',
        display: 'flex', flexDirection: 'column', gap: 6,
      }}>
        {(memory || []).length === 0
          ? <p style={{ color: 'var(--muted)', fontSize: '0.82rem' }}>No memory entries yet.</p>
          : (memory || []).slice(0, 30).map((m, i) => (
            <div key={i} style={{
              background: 'var(--bg)', border: '1px solid var(--border)',
              borderRadius: 6, padding: '7px 10px', fontSize: '0.78rem',
              color: 'var(--muted)',
            }}>
              <span style={{ color: 'var(--text)', fontWeight: 600, fontSize: '0.75rem', marginRight: 6 }}>
                {m.role || '?'}
              </span>
              {String(m.text || m.contribution || '').slice(0, 200)}
            </div>
          ))
        }
      </div>
    </div>
  );
}
