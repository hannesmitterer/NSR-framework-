import React from 'react';

function repColor(score) {
  if (score >= 0.7) return 'var(--green)';
  if (score >= 0.4) return 'var(--yellow)';
  return 'var(--red)';
}

export default function ReputationPanel({ reputation }) {
  const entries = Object.entries(reputation || {});
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
        ⭐ Reputation Scores
      </div>
      <div style={{ padding: '14px 16px' }}>
        {entries.length === 0
          ? <p style={{ color: 'var(--muted)', fontSize: '0.82rem' }}>No data yet.</p>
          : entries.map(([id, score]) => (
            <div key={id} style={{
              display: 'flex', alignItems: 'center', gap: 10, marginBottom: 10,
            }}>
              <div style={{ width: 80, fontSize: '0.82rem', fontWeight: 600,
                overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}
                title={id}>
                {id.slice(0, 8)}
              </div>
              <div style={{
                flex: 1, height: 10, background: 'var(--bg)',
                borderRadius: 5, overflow: 'hidden',
              }}>
                <div style={{
                  width: `${(score * 100).toFixed(1)}%`,
                  height: '100%', borderRadius: 5,
                  background: repColor(score),
                  transition: 'width 0.4s',
                }} />
              </div>
              <div style={{ width: 38, textAlign: 'right',
                fontSize: '0.8rem', color: 'var(--muted)' }}>
                {score.toFixed(2)}
              </div>
            </div>
          ))
        }
      </div>
    </div>
  );
}
