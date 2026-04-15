/**
 * Playwright global teardown — runs ONCE after all workers finish.
 * Cleans up test-created campaigns so they don't accumulate.
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

export default async function globalTeardown() {
  try {
    const resp = await fetch(`${API_BASE}/campaigns`)
    if (!resp.ok) return
    const campaigns = await resp.json() as Array<{ id: string; name: string }>

    const kept = new Set<string>()
    const toDelete: string[] = []

    for (const c of campaigns) {
      if (FEATURED.has(c.name) && !kept.has(c.name)) {
        kept.add(c.name)
      } else {
        toDelete.push(c.id)
      }
    }

    if (toDelete.length === 0) return

    console.log(`[global-teardown] Cleaning up ${toDelete.length} test campaigns...`)
    await Promise.all(
      toDelete.map(id =>
        fetch(`${API_BASE}/campaigns/${id}`, { method: 'DELETE' }).catch(() => {})
      )
    )
    console.log(`[global-teardown] Cleanup complete`)
  } catch (err) {
    console.warn('[global-teardown] Cleanup failed (non-fatal):', err)
  }
}
