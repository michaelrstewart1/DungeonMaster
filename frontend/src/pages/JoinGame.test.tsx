import { beforeEach, describe, expect, it, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { JoinGame } from './JoinGame';

const mockNavigate = vi.fn();

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<typeof import('react-router-dom')>('react-router-dom');
  return { ...actual, useNavigate: () => mockNavigate };
});

function json(body: unknown, status = 200): Response {
  return {
    ok: status >= 200 && status < 300,
    status,
    json: async () => body,
  } as Response;
}

describe('JoinGame hero picker', () => {
  beforeEach(() => {
    mockNavigate.mockReset();
    localStorage.clear();
    sessionStorage.clear();
    vi.stubGlobal('fetch', vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      if (url.endsWith('/game/join')) {
        return json({
          session_id: 'sess-live',
          player_id: 'p-aria',
          campaign_id: 'camp-1',
          rejoined: false,
        });
      }
      if (url.includes('/characters?campaign_id=')) {
        return json([{
          id: 'char-thorne',
          name: 'Thorne Ironfist',
          race: 'dwarf',
          class_name: 'fighter',
          level: 3,
          portrait_url: '/portraits/thorne.jpg',
        }]);
      }
      if (url.endsWith('/players')) {
        return json({
          players: [{ id: 'p-host', name: 'Host', character_id: 'char-thorne' }],
        });
      }
      if (url.endsWith('/characters') && init?.method === 'POST') {
        const body = JSON.parse(String(init.body));
        return json({ id: 'char-lyra', ...body });
      }
      if (url.endsWith('/select-character')) {
        return json({ ok: true });
      }
      return json({ detail: 'not found' }, 404);
    }));
  });

  it('offers unclaimed pre-made heroes and hides the one already in the party', async () => {
    render(
      <MemoryRouter initialEntries={['/join?code=LIVE']}>
        <JoinGame />
      </MemoryRouter>,
    );

    fireEvent.change(screen.getByPlaceholderText(/Cohen, Brody, Kit/), { target: { value: 'Aria' } });
    fireEvent.click(screen.getByRole('button', { name: /Enter the Dungeon/ }));

    expect(await screen.findByTestId('join-hero-premade-lyra')).toBeInTheDocument();
    expect(screen.queryByText('Thorne Ironfist')).not.toBeInTheDocument();
    expect(screen.getByText('Lyra Moonwhisper')).toBeInTheDocument();

    fireEvent.click(screen.getByTestId('join-hero-premade-lyra'));

    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith('/play/sess-live');
    });

    const calls = (fetch as unknown as ReturnType<typeof vi.fn>).mock.calls;
    const create = calls.find((call) => String(call[0]).endsWith('/characters') && call[1]?.method === 'POST');
    expect(create).toBeTruthy();
    const created = JSON.parse(String(create![1].body));
    expect(created.name).toBe('Lyra Moonwhisper');
    expect(created.campaign_id).toBe('camp-1');
    expect(created.portrait_url).toBe('/portraits/lyra.jpg');
    expect(created.id).toBeUndefined();

    const claim = calls.find((call) => String(call[0]).endsWith('/select-character'));
    expect(JSON.parse(String(claim![1].body)).character_id).toBe('char-lyra');
  });
});
