import React, { useCallback, useEffect, useReducer, useRef } from 'react';
import './index.css';
import MessageFeed from './components/MessageFeed';
import ReputationPanel from './components/ReputationPanel';
import ChainPanel from './components/ChainPanel';
import MemoryPanel from './components/MemoryPanel';
import InjectForm from './components/InjectForm';
import NetworkGraph from './components/NetworkGraph';

// ---------------------------------------------------------------------------
// State management
// ---------------------------------------------------------------------------
const MAX_MESSAGES = 100;
const MAX_MEMORY = 50;

const initialState = {
  connected: false,
  messages: [],
  reputation: {},
  chain: { length: 0, last_hash: 'GENESIS' },
  memory: [],
};

function reducer(state, action) {
  switch (action.type) {
    case 'CONNECTED':
      return { ...state, connected: true };
    case 'DISCONNECTED':
      return { ...state, connected: false };
    case 'SNAPSHOT':
      return {
        ...state,
        messages: (action.payload.messages || []).slice(-MAX_MESSAGES),
        reputation: action.payload.reputation || {},
        chain: action.payload.chain || state.chain,
        memory: (action.payload.memory || []).slice(-MAX_MEMORY),
      };
    case 'MESSAGE': {
      const msg = action.payload;
      const messages = [msg, ...state.messages].slice(0, MAX_MESSAGES);
      const reputation = { ...state.reputation };
      if (msg.node_id && msg.reputation != null) {
        reputation[msg.node_id] = msg.reputation;
      }
      const chain = msg.chain_len != null
        ? { ...state.chain, length: msg.chain_len }
        : state.chain;
      return { ...state, messages, reputation, chain };
    }
    case 'REPUTATION':
      return { ...state, reputation: { ...state.reputation, ...action.payload } };
    case 'MEMORY': {
      const memory = [action.payload, ...state.memory].slice(0, MAX_MEMORY);
      return { ...state, memory };
    }
    case 'CHAIN':
      return { ...state, chain: { ...state.chain, ...action.payload } };
    default:
      return state;
  }
}

// ---------------------------------------------------------------------------
// App
// ---------------------------------------------------------------------------
export default function App() {
  const [state, dispatch] = useReducer(reducer, initialState);
  const wsRef = useRef(null);
  const reconnectTimer = useRef(null);

  const connect = useCallback(() => {
    const proto = window.location.protocol === 'https:' ? 'wss' : 'ws';
    const wsUrl = `${proto}://${window.location.host}/ws`;
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => dispatch({ type: 'CONNECTED' });
    ws.onclose = () => {
      dispatch({ type: 'DISCONNECTED' });
      reconnectTimer.current = setTimeout(connect, 3000);
    };
    ws.onerror = () => ws.close();
    ws.onmessage = (evt) => {
      let msg;
      try { msg = JSON.parse(evt.data); } catch (err) { console.warn('Failed to parse WS message:', err); return; }
      const { type, payload } = msg;
      if (type === 'ping') return;
      if (type === 'snapshot') { dispatch({ type: 'SNAPSHOT', payload }); return; }
      if (type === 'message') { dispatch({ type: 'MESSAGE', payload }); return; }
      if (type === 'reputation') { dispatch({ type: 'REPUTATION', payload }); return; }
      if (type === 'memory') { dispatch({ type: 'MEMORY', payload }); return; }
      // raw agent manifest
      dispatch({ type: 'MESSAGE', payload: msg });
    };
  }, []);

  useEffect(() => {
    connect();
    return () => {
      clearTimeout(reconnectTimer.current);
      wsRef.current?.close();
    };
  }, [connect]);

  // Polling fallback
  useEffect(() => {
    const poll = async () => {
      try {
        const r = await fetch('/state');
        const s = await r.json();
        dispatch({ type: 'REPUTATION', payload: s.reputation || {} });
        if (s.chain) dispatch({ type: 'CHAIN', payload: s.chain });
      } catch (_) {}
    };
    const id = setInterval(poll, 6000);
    return () => clearInterval(id);
  }, []);

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      <Header connected={state.connected} />
      <main style={{ flex: 1, padding: '24px 28px', display: 'grid', gap: 18,
        gridTemplateColumns: 'repeat(auto-fill, minmax(380px, 1fr))' }}>

        <div style={{ gridColumn: 'span 2' }}>
          <NetworkGraph reputation={state.reputation} messages={state.messages} />
        </div>

        <div style={{ gridColumn: 'span 2' }}>
          <MessageFeed messages={state.messages} />
        </div>

        <ReputationPanel reputation={state.reputation} />
        <ChainPanel chain={state.chain} />
        <MemoryPanel memory={state.memory} />
        <InjectForm />
      </main>
      <footer style={{ textAlign: 'center', padding: 18,
        fontSize: '0.75rem', color: 'var(--muted)',
        borderTop: '1px solid var(--border)' }}>
        Lex Amoris Ecosystem v2 · Kosymbiosis · [EVOLUTION_COMPLETE] ❤️
      </footer>
    </div>
  );
}

function Header({ connected }) {
  return (
    <header style={{ display: 'flex', alignItems: 'center', gap: 12,
      padding: '18px 28px', borderBottom: '1px solid var(--border)',
      background: 'var(--surface)' }}>
      <h1 style={{ fontSize: '1.3rem', fontWeight: 600 }}>🌿 Lex Amoris Network</h1>
      <span style={{
        padding: '2px 10px', borderRadius: 20, fontSize: '0.75rem', fontWeight: 600,
        background: connected ? 'var(--green)' : 'var(--red)', color: '#000',
      }}>
        {connected ? 'LIVE' : 'disconnected'}
      </span>
    </header>
  );
}
