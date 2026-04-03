import React, { useState } from 'react';

const ROLES = ['RADICE', 'SILENZIO', 'NODO', 'external'];

export default function InjectForm() {
  const [role, setRole] = useState('RADICE');
  const [data, setData] = useState('');
  const [status, setStatus] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!data.trim()) return;
    setLoading(true);
    try {
      const r = await fetch('/message', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ role, data }),
      });
      const j = await r.json();
      setStatus(j.ok ? '✅ Sent!' : '❌ Failed');
      if (j.ok) setData('');
    } catch (err) {
      setStatus(`❌ ${err.message}`);
    } finally {
      setLoading(false);
      setTimeout(() => setStatus(''), 3000);
    }
  };

  const inputStyle = {
    background: 'var(--bg)', color: 'var(--text)',
    border: '1px solid var(--border)', borderRadius: 6,
    padding: '8px 10px', fontSize: '0.82rem', fontFamily: 'inherit',
    width: '100%',
  };

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
        💬 Inject Message
      </div>
      <form onSubmit={handleSubmit} style={{
        padding: '14px 16px', display: 'flex', flexDirection: 'column', gap: 10,
      }}>
        <select value={role} onChange={e => setRole(e.target.value)} style={inputStyle}>
          {ROLES.map(r => <option key={r} value={r}>{r}</option>)}
        </select>
        <textarea
          value={data}
          onChange={e => setData(e.target.value)}
          rows={3}
          placeholder="Enter message…"
          style={{ ...inputStyle, resize: 'vertical' }}
        />
        <button
          type="submit"
          disabled={loading}
          style={{
            padding: '9px 18px', background: 'var(--accent)', color: '#000',
            border: 'none', borderRadius: 6, fontWeight: 700, cursor: 'pointer',
            fontSize: '0.85rem', alignSelf: 'flex-start',
            opacity: loading ? 0.6 : 1,
          }}
        >
          {loading ? 'Sending…' : 'Send to Network'}
        </button>
        {status && (
          <p style={{ fontSize: '0.75rem', color: 'var(--muted)' }}>{status}</p>
        )}
      </form>
    </div>
  );
}
