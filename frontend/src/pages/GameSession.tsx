import { useState, useEffect, useRef, useCallback } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { uuid } from '../utils/uuid'
import { getGameState, submitAction, getCampaign, getSessionGreeting, getSessionRecap, getCharacters } from '../api/client'
import { GameWebSocket } from '../api/websocket'
import { GameChat, type ChatMessage } from '../components/GameChat'
import { DiceRoller } from '../components/DiceRoller'
import { InitiativeTracker, type CombatantDisplay } from '../components/InitiativeTracker'
import { DMAvatar } from '../components/DMAvatar'
import { AudioControls } from '../components/AudioControls'
import { PartyStatus } from '../components/PartyStatus'
import { ScreenEffects, type EffectType } from '../components/ScreenEffects'
import { AtmosphericBackground, type Atmosphere } from '../components/AtmosphericBackground'
import BattleMap from '../components/BattleMap'
import TokenLayer from '../components/TokenLayer'
import type { TokenInfo } from '../components/TokenLayer'
import FogOfWar from '../components/FogOfWar'
import { AdventureLog } from '../components/AdventureLog'
import type { Quest, AdventureEntry, LootItem } from '../components/AdventureLog'
import { CombatLog, type CombatLogEntry } from '../components/CombatLog'
import { NPCDialogue, parseNPCDialogue } from '../components/NPCDialogue'
import type { NPCType } from '../components/NPCDialogue'
import { SessionRecap } from '../components/SessionRecap'
import PartyInventory from '../components/PartyInventory'
import { SceneArt, detectScene } from '../components/SceneArt'
import type { SceneType } from '../components/SceneArt'
import { EncounterPanel } from '../components/EncounterPanel'
import { DeathSaveTracker } from '../components/DeathSaveTracker'
import { SpellSlotTracker } from '../components/SpellSlotTracker'
import { MiniMap } from '../components/MiniMap'
import { AchievementToast, checkAchievements } from '../components/AchievementToast'
import type { Achievement } from '../components/AchievementToast'
import { NPCJournal, detectNPCMention } from '../components/NPCJournal'
import { EnvironmentPanel } from '../components/EnvironmentPanel'
import type { GameState, GameMap, DiceResult, Character } from '../types'
import './GameSession.css'

function formatTime(seconds: number): string {
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  const s = seconds % 60
  return h > 0
    ? `${h}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
    : `${m}:${String(s).padStart(2, '0')}`
}

export function GameSession() {
  const { sessionId } = useParams<{ sessionId: string }>()
  const navigate = useNavigate()

  const [gameState, setGameState] = useState<GameState | null>(null)
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [combatants, setCombatants] = useState<CombatantDisplay[]>([])
  const [lastDiceResult, setLastDiceResult] = useState<DiceResult | null>(null)
  const [mapData, _setMapData] = useState<GameMap | null>(null)
  const [avatarState, setAvatarState] = useState({ expression: 'neutral', isSpeaking: false, amplitude: 0 })
  const [audioState, setAudioState] = useState({ micOn: false, muted: false })
  const [selectedToken, setSelectedToken] = useState<string | null>(null)
  const [fogRevealed, setFogRevealed] = useState<Set<string>>(new Set())
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [wsConnected, setWsConnected] = useState(false)
  const [campaignName, setCampaignName] = useState<string>('Game Session')
  const [waitingForDM, setWaitingForDM] = useState(false)
  const [sessionTime, setSessionTime] = useState(0)
  const [showKeyboardHelp, setShowKeyboardHelp] = useState(false)
  const [partyCharacters, setPartyCharacters] = useState<Character[]>([])
  const [activeEffect, setActiveEffect] = useState<EffectType>(null)
  const [atmosphere, setAtmosphere] = useState<Atmosphere>('neutral')
  const [adventureLogOpen, setAdventureLogOpen] = useState(false)
  const [quests, setQuests] = useState<Quest[]>([])
  const [adventureEntries, setAdventureEntries] = useState<AdventureEntry[]>([])
  const [lootItems, setLootItems] = useState<LootItem[]>([])
  const [combatLogEntries, setCombatLogEntries] = useState<CombatLogEntry[]>([])
  const [combatRound, setCombatRound] = useState(0)
  const [npcDialogue, setNpcDialogue] = useState<{ npcName: string; npcType: NPCType; dialogue: string } | null>(null)
  const [showRecap, setShowRecap] = useState(false)
  const [recapText, setRecapText] = useState('')
  const [showInventory, setShowInventory] = useState(false)
  const [currentScene, setCurrentScene] = useState<SceneType>('tavern')
  const [showDeathSaves, setShowDeathSaves] = useState(false)
  const [showSpellSlots, setShowSpellSlots] = useState(false)
  const [showNPCJournal, setShowNPCJournal] = useState(false)
  const [achievements, setAchievements] = useState<Achievement[]>([])
  const [unlockedAchievements, setUnlockedAchievements] = useState<Set<string>>(new Set())
  const turnCounterRef = useRef(0)
  const partyCharsRef = useRef<Character[]>([])

  const wsRef = useRef<GameWebSocket | null>(null)
  const audioWsRef = useRef<WebSocket | null>(null)
  const audioChunksRef = useRef<Uint8Array[]>([])
  const isMutedRef = useRef(false)

  // Keep ref in sync for WS callback closure
  useEffect(() => { partyCharsRef.current = partyCharacters }, [partyCharacters])

  // Detect screen effect from DM narration text
  const detectEffect = useCallback((text: string) => {
    const lower = text.toLowerCase()
    if (/natural 20|critical hit|critical strike/.test(lower)) {
      setActiveEffect('nat20')
    } else if (/level up|leveled up|gained a level/.test(lower)) {
      setActiveEffect('levelup')
    } else if (/takes? \d+ damage|hits you|struck|you take damage/.test(lower)) {
      setActiveEffect('damage')
    } else if (/casts? |spell|magical|arcane|conjure|invoke/.test(lower)) {
      setActiveEffect('spell')
    }
  }, [])

  // Detect atmosphere from mood field or narration text
  const detectAtmosphere = useCallback((mood?: string, text?: string) => {
    if (mood && ['dark', 'warm', 'peaceful', 'combat', 'mystical', 'neutral'].includes(mood)) {
      setAtmosphere(mood as Atmosphere)
      return
    }
    if (!text) return
    const lower = text.toLowerCase()
    if (/combat begins|initiative|attack|sword|fight|battle|enemy/.test(lower)) {
      setAtmosphere('combat')
    } else if (/tavern|inn|fire|hearth|warm|ale|drink|barkeep/.test(lower)) {
      setAtmosphere('warm')
    } else if (/dungeon|cave|dark|shadow|underground|crypt|tomb/.test(lower)) {
      setAtmosphere('dark')
    } else if (/forest|grove|meadow|stream|birds|peaceful|glade/.test(lower)) {
      setAtmosphere('peaceful')
    } else if (/magic|arcane|rune|enchant|mystical|ethereal|portal|wizard/.test(lower)) {
      setAtmosphere('mystical')
    }
  }, [])

  // Play DM text via TTS audio websocket
  const speakText = useCallback((text: string) => {
    if (isMutedRef.current) return
    const ws = audioWsRef.current
    if (ws && ws.readyState === WebSocket.OPEN) {
      audioChunksRef.current = []
      ws.send(JSON.stringify({ type: 'synthesize', text }))
    }
  }, [])

  // Session timer
  useEffect(() => {
    const timer = setInterval(() => setSessionTime(t => t + 1), 1000)
    return () => clearInterval(timer)
  }, [])

  // Categorize DM message and create adventure log entries
  const processDMMessage = useCallback((text: string) => {
    const lower = text.toLowerCase()
    turnCounterRef.current += 1
    const turn = turnCounterRef.current

    // Detect entry type from keywords
    let entryType: AdventureEntry['type'] = 'dialogue'
    if (/attack|combat|damage|fight|strike|slash|stab|arrow|hit|wound|battle|sword/.test(lower)) {
      entryType = 'combat'
    } else if (/find|discover|notice|reveal|uncover|spot|detect|hidden|secret/.test(lower)) {
      entryType = 'discovery'
    } else if (/quest|mission|task|objective|assignment|duty|charge/.test(lower)) {
      entryType = 'quest'
    } else if (/gold|sword|potion|item|treasure|loot|coin|gem|weapon|armor|ring|amulet|scroll/.test(lower)) {
      entryType = 'loot'
    } else if (/rest|camp|sleep|recover|heal|long rest|short rest/.test(lower)) {
      entryType = 'rest'
    } else if (/talk|says|speaks|ask|tell|reply|respond|greet|whisper|shout/.test(lower)) {
      entryType = 'dialogue'
    }

    const summary = text.length > 100 ? text.slice(0, 100) + '...' : text

    const entry: AdventureEntry = {
      id: uuid(),
      type: entryType,
      summary,
      turnNumber: turn,
      timestamp: new Date(),
    }
    setAdventureEntries(prev => [...prev, entry])

    // Auto-extract quests from messages mentioning quest keywords
    if (/quest|mission|task/.test(lower)) {
      const questMatch = text.match(/(?:quest|mission|task)[:\s]+["']?([^"'.!?]+)/i)
      if (questMatch) {
        const questTitle = questMatch[1].trim().slice(0, 60)
        setQuests(prev => {
          if (prev.some(q => q.title.toLowerCase() === questTitle.toLowerCase())) return prev
          return [...prev, {
            id: uuid(),
            title: questTitle,
            description: summary,
            status: 'active' as const,
            turnAdded: turn,
          }]
        })
      }
    }

    // Auto-extract loot items from messages
    const lootPatterns = [
      /(?:find|discover|receive|obtain|pick up|loot)\s+(?:a\s+|an\s+|the\s+)?(.+?)(?:\.|!|,|$)/i,
    ]
    if (entryType === 'loot') {
      for (const pattern of lootPatterns) {
        const match = text.match(pattern)
        if (match) {
          const itemName = match[1].trim().slice(0, 50)
          if (itemName.length > 2) {
            let rarity: LootItem['rarity'] = 'common'
            if (/legendary|artifact/.test(lower)) rarity = 'legendary'
            else if (/very rare/.test(lower)) rarity = 'very-rare'
            else if (/rare/.test(lower)) rarity = 'rare'
            else if (/uncommon|magic|enchanted/.test(lower)) rarity = 'uncommon'

            setLootItems(prev => [...prev, {
              id: uuid(),
              name: itemName,
              rarity,
              description: summary,
              turnFound: turn,
            }])
            break
          }
        }
      }
    }

    // Detect NPC dialogue from quoted speech
    const npc = parseNPCDialogue(text)
    if (npc) {
      setNpcDialogue(npc)
    }
  }, [])

  // Parse DM narration text into combat log entries during combat
  const extractCombatLogEntries = useCallback((text: string) => {
    if (gameState?.phase !== 'combat') return
    const lower = text.toLowerCase()
    const now = Date.now()
    const newEntries: CombatLogEntry[] = []

    // Detect defeat
    if (/defeated|falls\s+(dead|unconscious)|dies|has been slain|killed/.test(lower)) {
      const match = text.match(/(\w+)\s+(?:has been defeated|falls|dies|has been slain|is killed)/i)
      newEntries.push({
        id: uuid(),
        type: 'defeat',
        text: match ? `${match[1]} has been defeated!` : 'A creature has been defeated!',
        timestamp: now,
      })
    }

    // Detect spell
    if (/casts?\s|spell|cantrip/.test(lower)) {
      const match = text.match(/(\w+)\s+casts?\s+(.+?)(?:\s+at|\s+on|\.|!|,|$)/i)
      newEntries.push({
        id: uuid(),
        type: 'spell',
        text: match ? `${match[1]} casts ${match[2].trim()}` : 'A spell is cast!',
        timestamp: now,
      })
    }

    // Detect saving throw
    if (/saving throw|saves?\s+(?:against|vs|DC)/i.test(lower)) {
      const success = /succeeds|success|makes the save/.test(lower)
      const fail = /fails|failure|fails the save/.test(lower)
      const match = text.match(/(\w+)\s+(?:makes?\s+a\s+)?(\w+)\s+sav/i)
      newEntries.push({
        id: uuid(),
        type: 'save',
        text: match ? `${match[1]} makes a ${match[2].toUpperCase()} save` : 'A saving throw is made',
        result: success ? 'success' : fail ? 'fail' : undefined,
        timestamp: now,
      })
    }

    // Detect attack
    if (/attacks?\s|strikes?\s|swings?\s/.test(lower)) {
      const hit = /hits?!|strikes? true|lands/.test(lower)
      const miss = /miss(?:es)?!|goes wide|dodges/.test(lower)
      const crit = /critical|nat(?:ural)?\s*20/.test(lower)
      const match = text.match(/(\w+)\s+(?:attacks?|strikes?|swings? at)\s+(?:the\s+)?(\w+)/i)
      newEntries.push({
        id: uuid(),
        type: 'attack',
        text: match ? `${match[1]} attacks ${match[2]}` : 'An attack is made',
        result: crit ? 'crit' : hit ? 'hit' : miss ? 'miss' : undefined,
        timestamp: now,
      })
    }

    // Detect damage
    if (/deals?\s.*damage|damage[ds]?\s|takes?\s+\d+\s/.test(lower)) {
      const match = text.match(/(?:deals?\s+)?(\d+)\s+(\w+)\s+damage/i)
        || text.match(/takes?\s+(\d+)\s+(?:points?\s+of\s+)?(\w+)?\s*damage/i)
      newEntries.push({
        id: uuid(),
        type: 'damage',
        text: match ? `${match[1]} ${match[2] || ''} damage dealt`.trim() : 'Damage is dealt',
        details: match ? `${match[1]} ${match[2] || ''} damage`.trim() : undefined,
        timestamp: now,
      })
    }

    // Detect conditions
    if (/is now\s+\w+ed|becomes?\s+(?:stunned|frightened|poisoned|paralyzed|restrained|blinded|charmed|prone|incapacitated)/.test(lower)) {
      const match = text.match(/(\w+)\s+(?:is now|becomes?)\s+(\w+)/i)
      newEntries.push({
        id: uuid(),
        type: 'condition',
        text: match ? `${match[1]} is now ${match[2]}` : 'A condition is applied',
        timestamp: now,
      })
    }

    if (newEntries.length > 0) {
      setCombatLogEntries(prev => [...prev, ...newEntries])
    }
  }, [gameState?.phase])

  // Track round changes from combat state
  useEffect(() => {
    const round = gameState?.combat_state?.round_number
    if (round != null && round !== combatRound) {
      setCombatRound(round)
      if (round > 0) {
        setCombatLogEntries(prev => [...prev, {
          id: uuid(),
          type: 'round',
          text: `Round ${round}`,
          timestamp: Date.now(),
        }])
      }
    }
  }, [gameState?.combat_state?.round_number, combatRound])

  // ? key toggles keyboard help, J toggles adventure log
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) return
      if (e.key === '?') setShowKeyboardHelp(v => !v)
      if (e.key === 'Escape') {
        setShowKeyboardHelp(false)
        setAdventureLogOpen(false)
        setShowInventory(false)
        setShowDeathSaves(false)
        setShowSpellSlots(false)
        setShowNPCJournal(false)
      }
      if (e.key === 'j' || e.key === 'J') setAdventureLogOpen(v => !v)
      if (e.key === 'i' || e.key === 'I') setShowInventory(v => !v)
      if (e.key === 'n' || e.key === 'N') setShowNPCJournal(v => !v)
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [])

  // Derive token info from map tokens for the TokenLayer component
  const tokenInfos: TokenInfo[] = (mapData?.tokens || []).map((t) => ({
    entity_id: t.entity_id,
    name: t.entity_id,
    x: t.x,
    y: t.y,
    hp: 10,
    max_hp: 10,
    is_player: true,
  }))

  // Derive fog grid from map data for the FogOfWar component
  const fogGrid: string[][] = mapData
    ? mapData.terrain.map((row) => row.map((cell) => cell))
    : []

   const loadGameState = useCallback(async () => {
    if (!sessionId) return
    setLoading(true)
    setError(null)
    try {
      const state = await getGameState(sessionId)
      setGameState(state)
      // Fetch campaign name for the header
      if (state.campaign_id) {
        try {
          const campaign = await getCampaign(state.campaign_id)
          setCampaignName(campaign.name)
        } catch { /* fallback to default */ }
        try {
          const chars = await getCharacters(state.campaign_id)
          setPartyCharacters(chars)
        } catch { /* party status will just be empty */ }
      }
      // Check for session recap (cinematic "Previously on..." overlay)
      try {
        const recap = await getSessionRecap(sessionId)
        if (recap.has_recap && recap.recap_text) {
          setRecapText(recap.recap_text)
          setShowRecap(true)
        }
      } catch { /* no recap available — skip */ }
      // Show typing indicator while the DM greeting loads
      setLoading(false)
      setWaitingForDM(true)
      
      // Fetch the AI greeting (with fallback)
      let greeting = ''
      try {
        const greetingPromise = getSessionGreeting(sessionId)
        const timeoutPromise = new Promise<string>((_, reject) =>
          setTimeout(() => reject(new Error('timeout')), 20000)
        )
        greeting = await Promise.race([greetingPromise, timeoutPromise])
      } catch { /* AI greeting unavailable — use static fallback */ }

      if (!greeting || !greeting.trim()) {
        const name = campaignName || 'this realm'
        greeting = `Welcome, adventurers, to ${name}. The shadows stir and ancient forces take notice of your arrival. Steel yourselves — your legend begins tonight.`
      }

      setWaitingForDM(false)
      setMessages([{ role: 'dm', text: greeting, timestamp: Date.now() }])
      processDMMessage(greeting)
      speakText(greeting)
      if (state.combat_state) {
        setCombatants(
          state.combat_state.initiative_order.map((id, idx) => ({
            id,
            name: id,
            initiative: state.combat_state!.initiative_order.length - idx,
            hp: 10,
            max_hp: 10,
            is_current: idx === state.combat_state!.current_turn_index,
          }))
        )
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load game state')
    } finally {
      setLoading(false)
    }
  }, [sessionId, speakText, processDMMessage])

  useEffect(() => {
    loadGameState()

    if (!sessionId) return

    // Audio WebSocket for TTS voice
    const wsBase = import.meta.env.VITE_WS_URL || `ws://${window.location.host}`
    const audioWs = new WebSocket(`${wsBase}/ws/audio/${sessionId}`)
    audioWsRef.current = audioWs
    audioWs.binaryType = 'arraybuffer'
    audioWs.onmessage = (event) => {
      if (event.data instanceof ArrayBuffer) {
        // Accumulate audio chunks
        audioChunksRef.current.push(new Uint8Array(event.data))
      } else {
        // JSON message — check for audio_done signal
        try {
          const msg = JSON.parse(event.data as string)
          if (msg.type === 'audio_done' && audioChunksRef.current.length > 0) {
            const total = audioChunksRef.current.reduce((acc, c) => acc + c.length, 0)
            const merged = new Uint8Array(total)
            let offset = 0
            for (const chunk of audioChunksRef.current) { merged.set(chunk, offset); offset += chunk.length }
            audioChunksRef.current = []
            const blob = new Blob([merged], { type: 'audio/mpeg' })
            const url = URL.createObjectURL(blob)
            const audio = new Audio(url)
            audio.onended = () => URL.revokeObjectURL(url)
            audio.play().catch(() => {})
          }
        } catch { /* ignore non-JSON */ }
      }
    }

    const ws = new GameWebSocket(sessionId)
    wsRef.current = ws

    const unsubMessage = ws.onMessage((msg) => {
      switch (msg.type) {
        case 'game_state':
          setGameState(msg.payload as GameState)
          break
        case 'turn_result': {
          const result = msg.payload as { narration?: string; narrative?: string; mood?: string; dice_results?: DiceResult[] }
          const text = result.narration || result.narrative || 'The DM ponders...'
          setMessages((prev) => [...prev, { role: 'dm', text, timestamp: Date.now() }])
          processDMMessage(text)
          extractCombatLogEntries(text)
          setAvatarState((prev) => ({ ...prev, expression: 'speaking', isSpeaking: true }))
          setTimeout(() => setAvatarState((prev) => ({ ...prev, isSpeaking: false, expression: 'neutral' })), 2000)
          speakText(text)
          detectEffect(text)
          detectAtmosphere(result.mood, text)
          setCurrentScene(detectScene(text))
          // Check for NPC mentions
          const npcMention = detectNPCMention(text)
          if (npcMention) {
            // NPC detected — journal will pick it up
          }
          // Check achievements
          turnCounterRef.current++
          const newAchievements = checkAchievements(messages, turnCounterRef.current, undefined, {
            natural20: text.toLowerCase().includes('natural 20') || text.toLowerCase().includes('critical hit'),
            naturalOne: text.toLowerCase().includes('natural 1') || text.toLowerCase().includes('critical fail'),
          })
          const fresh = newAchievements.filter(a => !unlockedAchievements.has(a.id))
          if (fresh.length > 0) {
            setAchievements(prev => [...prev, ...fresh])
            setUnlockedAchievements(prev => new Set([...prev, ...fresh.map(a => a.id)]))
          }
          if (result.dice_results?.length) {
            setLastDiceResult(result.dice_results[0])
          }
          break
        }
        case 'player_joined': {
          const heroName = partyCharsRef.current[0]?.name || 'A new adventurer'
          setMessages((prev) => [...prev, { role: 'dm', text: `${heroName} has joined the party!`, timestamp: Date.now() }])
          break
        }
        case 'player_left': {
          setMessages((prev) => [...prev, { role: 'dm', text: 'An adventurer has departed.', timestamp: Date.now() }])
          break
        }
        case 'error': {
          const data = msg.payload as { message: string }
          setMessages((prev) => [...prev, { role: 'dm', text: `Error: ${data.message}`, timestamp: Date.now() }])
          break
        }
      }
    })

    const unsubStatus = ws.onStatusChange(setWsConnected)
    ws.connect()

    return () => {
      unsubMessage()
      unsubStatus()
      ws.disconnect()
      wsRef.current = null
      audioWs.close()
      audioWsRef.current = null
    }
  }, [sessionId, loadGameState, speakText, extractCombatLogEntries])

  const handleSubmitAction = useCallback(async (action: string) => {
    if (!sessionId) return
    setMessages((prev) => [...prev, { role: 'player', text: action, timestamp: Date.now() }])
    setWaitingForDM(true)
    try {
      const result = await submitAction(sessionId, { type: 'interact', message: action })
      const text = result.narration || 'The DM ponders...'
      setMessages((prev) => [...prev, { role: 'dm', text, timestamp: Date.now() }])
      processDMMessage(text)
      extractCombatLogEntries(text)
      setAvatarState((prev) => ({ ...prev, expression: 'speaking', isSpeaking: true }))
      setTimeout(() => setAvatarState((prev) => ({ ...prev, isSpeaking: false, expression: 'neutral' })), 2000)
      speakText(text)
      detectEffect(text)
      detectAtmosphere(result.mood, text)
      setCurrentScene(detectScene(text))
    } catch {
      setMessages((prev) => [...prev, { role: 'dm', text: 'Failed to send action. Try again.', timestamp: Date.now() }])
    } finally {
      setWaitingForDM(false)
    }
  }, [sessionId, speakText, detectEffect, detectAtmosphere, processDMMessage, extractCombatLogEntries])

  const handleDiceRoll = useCallback((notation: string) => {
    if (wsRef.current) {
      wsRef.current.send({ type: 'dice_roll', notation })
    }
    // Local fallback for immediate feedback
    const match = notation.match(/(\d+)d(\d+)/)
    if (match) {
      const count = parseInt(match[1])
      const sides = parseInt(match[2])
      const rolls = Array.from({ length: count }, () => Math.floor(Math.random() * sides) + 1)
      const total = rolls.reduce((a, b) => a + b, 0)
      setLastDiceResult({
        notation,
        rolls,
        modifier: 0,
        total,
        is_critical: sides === 20 && rolls[0] === 20,
        is_fumble: sides === 20 && rolls[0] === 1,
      })
    }
  }, [])

  const handleCellClick = useCallback((x: number, y: number) => {
    if (selectedToken && wsRef.current) {
      wsRef.current.send({ type: 'token_move', entity_id: selectedToken, x, y })
    }
  }, [selectedToken])

  const handleMicToggle = useCallback(() => {
    setAudioState((prev) => ({ ...prev, micOn: !prev.micOn }))
  }, [])

  const handleMuteToggle = useCallback(() => {
    setAudioState((prev) => {
      isMutedRef.current = !prev.muted
      return { ...prev, muted: !prev.muted }
    })
  }, [])

  const handleFogReveal = useCallback((x: number, y: number) => {
    const key = `${x},${y}`
    setFogRevealed((prev) => {
      const next = new Set(prev)
      next.add(key)
      return next
    })
    if (wsRef.current) {
      wsRef.current.send({ type: 'fog_update', x, y, revealed: true })
    }
  }, [])

  if (loading) {
    return (
      <div className="game-session">
        <div className="game-loading" data-testid="game-loading">
          <div className="loading-orb">
            <div className="orb-inner" />
          </div>
          <p className="loading-text">Preparing your adventure...</p>
          <p className="loading-subtext">The Dungeon Master is setting the stage</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="game-session">
        <div className="game-error" data-testid="game-error">
          <span className="error-icon">⚠️</span>
          <h2>Something went wrong</h2>
          <p className="error-detail">{error}</p>
          <button className="btn-retry" onClick={loadGameState}>Try Again</button>
        </div>
      </div>
    )
  }

  return (
    <div className="game-session">
      {showRecap && (
        <SessionRecap
          campaignName={campaignName}
          recapText={recapText}
          onContinue={() => setShowRecap(false)}
        />
      )}
      <AtmosphericBackground atmosphere={atmosphere} />
      <SceneArt sceneType={currentScene} />
      <ScreenEffects
        activeEffect={activeEffect}
        onEffectComplete={() => setActiveEffect(null)}
      />
      {/* Header */}
      <header className="game-header">
        <div className="game-header-left">
          <button className="btn-back" onClick={() => navigate('/')} title="Back to campaigns">
            ← 
          </button>
          <h1>{campaignName}</h1>
        </div>
        <div className="session-info">
          {gameState && <span className="phase-badge">{gameState.phase}</span>}
          <span className="session-timer" title="Session duration">⏱ {formatTime(sessionTime)}</span>
          <button
            className={`btn-adventure-log ${adventureEntries.length > 0 ? 'has-updates' : ''}`}
            onClick={() => setAdventureLogOpen(v => !v)}
            title="Adventure Log (J)"
          >
            📜
          </button>
          <button
            className="btn-inventory"
            onClick={() => setShowInventory(v => !v)}
            title="Party Inventory (I)"
          >
            🎒
          </button>
          <button
            className="btn-npc-journal"
            onClick={() => setShowNPCJournal(v => !v)}
            title="NPC Journal (N)"
          >
            📖
          </button>
          <button
            className="btn-death-saves"
            onClick={() => setShowDeathSaves(v => !v)}
            title="Death Saves"
          >
            💀
          </button>
          <button
            className="btn-spell-slots"
            onClick={() => setShowSpellSlots(v => !v)}
            title="Spell Slots"
          >
            ✨
          </button>
          <button className="btn-keyboard-help" onClick={() => setShowKeyboardHelp(v => !v)} title="Keyboard shortcuts (?)">
            ⌨
          </button>
          <div className="ws-status">
            <span className={`ws-dot ${wsConnected ? 'connected' : 'disconnected'}`} />
            <span>{wsConnected ? 'Connected' : 'Connecting...'}</span>
          </div>
        </div>
      </header>

      {/* Game body */}
      <div className="game-body">
        {/* Left sidebar */}
        <aside className="game-sidebar-left">
          <DMAvatar
            expression={avatarState.expression}
            isSpeaking={avatarState.isSpeaking}
            mouthAmplitude={avatarState.amplitude}
          />
          <AudioControls
            isMicOn={audioState.micOn}
            isMuted={audioState.muted}
            onMicToggle={handleMicToggle}
            onMuteToggle={handleMuteToggle}
          />
          <PartyStatus characters={partyCharacters} />
          <MiniMap sceneType={currentScene} />
          <EnvironmentPanel sessionId={sessionId || ''} />
        </aside>

        {/* Main content */}
        <div className="game-main-content">
          {mapData && (
            <div className="map-area">
              <BattleMap
                map={mapData}
                selectedTokenId={selectedToken ?? undefined}
                onCellClick={handleCellClick}
              />
              <FogOfWar
                grid={fogGrid}
                revealed={fogRevealed}
                isDM={true}
                onReveal={handleFogReveal}
              />
              <TokenLayer
                tokens={tokenInfos}
                selectedTokenId={selectedToken ?? undefined}
                onSelect={setSelectedToken}
              />
            </div>
          )}
          <div className={`chat-area ${!mapData ? 'chat-area-full' : ''}`}>
            <GameChat messages={messages} onSubmitAction={handleSubmitAction} isWaitingForDM={waitingForDM} phase={gameState?.phase === 'combat' ? 'combat' : 'exploration'} />
          </div>
        </div>

        {/* Right panel */}
        <aside className="game-sidebar-right">
          <InitiativeTracker combatants={combatants} />
          <CombatLog entries={combatLogEntries} isInCombat={gameState?.phase === 'combat'} />
          <DiceRoller onRoll={handleDiceRoll} lastResult={lastDiceResult ?? undefined} />
          <EncounterPanel sessionId={sessionId || ''} partyLevel={partyCharacters[0]?.level || 1} />
        </aside>
      </div>

      {/* Keyboard shortcuts overlay */}
      {showKeyboardHelp && (
        <div className="keyboard-help-overlay" onClick={() => setShowKeyboardHelp(false)}>
          <div className="keyboard-help-panel" onClick={e => e.stopPropagation()}>
            <h3>⌨ Keyboard Shortcuts</h3>
            <div className="shortcut-list">
              <div className="shortcut-item"><kbd>1</kbd>–<kbd>6</kbd> <span>Roll dice (d4–d20)</span></div>
              <div className="shortcut-item"><kbd>Enter</kbd> <span>Send message</span></div>
              <div className="shortcut-item"><kbd>Shift+Enter</kbd> <span>New line in chat</span></div>
              <div className="shortcut-item"><kbd>J</kbd> <span>Toggle adventure log</span></div>
              <div className="shortcut-item"><kbd>I</kbd> <span>Toggle inventory</span></div>
              <div className="shortcut-item"><kbd>N</kbd> <span>Toggle NPC journal</span></div>
              <div className="shortcut-item"><kbd>?</kbd> <span>Toggle this help</span></div>
              <div className="shortcut-item"><kbd>Esc</kbd> <span>Close overlay</span></div>
            </div>
            <button className="btn-close-help" onClick={() => setShowKeyboardHelp(false)}>Close</button>
          </div>
        </div>
      )}

      {/* Adventure Log panel */}
      <AdventureLog
        isOpen={adventureLogOpen}
        onClose={() => setAdventureLogOpen(false)}
        quests={quests}
        entries={adventureEntries}
        loot={lootItems}
      />

      {/* NPC Dialogue overlay */}
      {npcDialogue && (
        <NPCDialogue
          npcName={npcDialogue.npcName}
          npcType={npcDialogue.npcType}
          dialogue={npcDialogue.dialogue}
          isActive={true}
          onClose={() => setNpcDialogue(null)}
        />
      )}

      {/* Party Inventory */}
      <PartyInventory
        sessionId={sessionId || ''}
        isOpen={showInventory}
        onClose={() => setShowInventory(false)}
      />

      {/* NPC Journal */}
      <NPCJournal
        sessionId={sessionId || ''}
        isOpen={showNPCJournal}
        onClose={() => setShowNPCJournal(false)}
      />

      {/* Death Save Tracker */}
      {showDeathSaves && (
        <DeathSaveTracker
          characterName={partyCharacters[0]?.name || 'Hero'}
          onClose={() => setShowDeathSaves(false)}
        />
      )}

      {/* Spell Slot Tracker */}
      {showSpellSlots && partyCharacters[0] && (
        <SpellSlotTracker
          character={partyCharacters[0]}
          onClose={() => setShowSpellSlots(false)}
        />
      )}

      {/* Achievement Toasts */}
      {achievements.map((a) => (
        <AchievementToast
          key={a.id}
          achievement={a}
          onDismiss={() => setAchievements(prev => prev.filter(x => x.id !== a.id))}
        />
      ))}
    </div>
  )
}
