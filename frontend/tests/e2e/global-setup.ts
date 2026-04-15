/**
 * Playwright global setup — runs ONCE before all workers.
 * Cleans up stale/duplicate campaigns from previous test runs.
 */

const API_BASE = process.env.E2E_BASE_URL
  ? `${process.env.E2E_BASE_URL.replace(/\/$/, '')}/api`
  : 'http://192.168.1.94/api'

const FEATURED = new Set([
  'Wrath of the Stormspire',
  'The Drowned Throne',
  'Ember of the Last God',
  'Carnival of Stolen Faces',
  'Iron Oath of Karak-Dum',
])

export default async function globalSetup() {
  try {
    const resp = await fetch(`${API_BASE}/campaigns`)
    if (!resp.ok) return
    const campaigns = await resp.json() as Array<{ id: string; name: string }>

    const kept = new Set<string>()
    const toDelete: string[] = []

    for (const c of campaigns) {
      if (FEATURED.has(c.name) && !kept.has(c.name)) {
        kept.add(c.name)
      } else if (FEATURED.has(c.name)) {
        toDelete.push(c.id)
      } else if (c.name.toLowerCase().startsWith('playtest') ||
                 c.name.toLowerCase().startsWith('test ') ||
                 c.name.toLowerCase().includes('timer test') ||
                 c.name.toLowerCase().includes('date-test') ||
                 c.name.toLowerCase().includes('tray test')) {
        toDelete.push(c.id)
      }
    }

    if (toDelete.length === 0) {
      console.log('[global-setup] No stale campaigns to clean up')
      return
    }

    console.log(`[global-setup] Cleaning up ${toDelete.length} stale campaigns...`)
    await Promise.all(
      toDelete.map(id =>
        fetch(`${API_BASE}/campaigns/${id}`, { method: 'DELETE' }).catch(() => {})
      )
    )
    console.log(`[global-setup] Cleanup complete`)
  } catch (err) {
    console.warn('[global-setup] Campaign cleanup failed (non-fatal):', err)
  }
}
