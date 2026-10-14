import { beforeEach, describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter, Route, Routes, useLocation } from 'react-router-dom';
import { PlayerView } from './PlayerView';
import { markClaimedThisSession, saveIdentity } from '../utils/playerIdentity';

vi.mock('../hooks/useGameSocket', () => ({
  useGameSocket: () => ({
    connected: false,
    messages: [],
    players: [],
    send: vi.fn(),
    sendChat: vi.fn(),
    sendAction: vi.fn(),
    joinAsPlayer: vi.fn(),
    connectionCount: 0,
  }),
}));

function LocationProbe() {
  const location = useLocation();
  return <div data-testid="loc">{location.pathname}{location.search}</div>;
}

describe('PlayerView claim gate', () => {
  beforeEach(() => {
    localStorage.clear();
    sessionStorage.clear();
    Element.prototype.scrollTo = () => {};
    vi.stubGlobal('WebSocket', class {
      binaryType = '';
      onopen: (() => void) | null = null;
      onmessage: (() => void) | null = null;
      onclose: (() => void) | null = null;
      close() { this.onclose?.(); }
      send() {}
    });
    vi.stubGlobal('fetch', vi.fn(async () => ({
      ok: true,
      status: 200,
      json: async () => ({}),
    })));
  });

  it('does not flash the play screen before this visit claims a hero', () => {
    saveIdentity({
      playerId: 'p-bram',
      playerName: 'Bram',
      sessionId: 'sess-live',
      characterId: 'char-thorne',
      roomCode: 'LIVE',
    });

    render(
      <MemoryRouter initialEntries={['/play/sess-live']}>
        <Routes>
          <Route path="/play/:sessionId" element={<PlayerView />} />
          <Route path="/join" element={<LocationProbe />} />
        </Routes>
      </MemoryRouter>,
    );

    expect(screen.queryByText(/The adventure awaits/i)).not.toBeInTheDocument();
    expect(screen.queryByText('Thorne')).not.toBeInTheDocument();
    expect(screen.getByTestId('loc').textContent).toBe('/join?code=LIVE');
  });

  it('renders the play screen after the claim step', () => {
    saveIdentity({
      playerId: 'p-bram',
      playerName: 'Bram',
      sessionId: 'sess-live',
      characterId: 'char-thorne',
      roomCode: 'LIVE',
    });
    markClaimedThisSession('sess-live');

    render(
      <MemoryRouter initialEntries={['/play/sess-live']}>
        <Routes>
          <Route path="/play/:sessionId" element={<PlayerView />} />
          <Route path="/join" element={<LocationProbe />} />
        </Routes>
      </MemoryRouter>,
    );

    expect(screen.getByText(/The adventure awaits/i)).toBeInTheDocument();
    expect(screen.queryByTestId('loc')).not.toBeInTheDocument();
  });
});