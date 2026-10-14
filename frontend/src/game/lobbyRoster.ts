/** One lobby row per player. Seats the server marked absent stay off the list. */

export interface LobbyPlayer {
  id: string;
  name: string;
  present?: boolean;
}

export function lobbyRoster<T extends LobbyPlayer>(players: T[]): T[] {
  const seen = new Set<string>();
  const rows: T[] = [];
  for (const player of players) {
    if (player.present === false) continue;
    const key = player.name.trim().toLowerCase();
    if (!key || seen.has(key)) continue;
    seen.add(key);
    rows.push(player);
  }
  return rows;
}
