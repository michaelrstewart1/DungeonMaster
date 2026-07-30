/** LLM player brains — each phone gets a persona that decides what to do,
 * phrased like a real player would type it. Uses the VM's Ollama. Any brain
 * failure falls back to a scripted playbook so the sim never stalls.
 */
import type { EventBus } from './events';

export interface Persona {
  playerName: string;
  characterName: string;
  style: string;
  /** fallback playbook when the LLM is unavailable */
  playbook: string[];
}

export const PERSONAS: Persona[] = [
  {
    playerName: 'Kit',
    characterName: 'Lyra Nightwhisper',
    style: 'cautious scout; scouts ahead, checks for traps, asks questions; short sentences',
    playbook: [
      'I scout ahead quietly, checking for traps',
      'I look for tracks or signs of danger',
      'I ready my bow and cover the party',
      'I listen at the door before we open it',
    ],
  },
  {
    playerName: 'Cohen',
    characterName: 'Thorin Ironforge',
    style: 'bold paladin; charges in, protects the weak, invokes his god dramatically',
    playbook: [
      'I stride forward with my warhammer raised, ready for anything',
      'I call on Moradin to light our way',
      'I put myself between the party and the danger',
      'I demand the creature surrender in the name of justice',
    ],
  },
  {
    playerName: 'Brody',
    characterName: 'Zephyr Stormcaller',
    style: 'chaotic sorcerer; flashy magic, jokes around, sometimes reckless',
    playbook: [
      'I send a few dancing sparks ahead to light the corridor',
      'I check the walls for magic auras',
      'I loudly ask if anything here wants to be turned into a frog',
      'I prepare a fire bolt just in case',
    ],
  },
  {
    playerName: 'Michael',
    characterName: 'Grimshaw the Unbroken',
    style: 'practical fighter; direct, tactical, watches the flanks',
    playbook: [
      'I take point and advance carefully',
      'I check our rear for anything following us',
      'I examine the room for anything useful',
      'I keep my greatsword ready and move up',
    ],
  },
];

const SYSTEM_PROMPT = (p: Persona) => `You are ${p.playerName}, a human playing D&D. \
Your character is ${p.characterName}. Play style: ${p.style}. \
Reply with ONE first-person action your character takes next, as you would type it \
on your phone during the game. Max 20 words. No quotes, no markdown, no explanations.`;

export class PersonaBrain {
  private history: string[] = [];
  private failCount = 0;
  private playbookIdx = 0;

  constructor(
    public persona: Persona,
    private ollamaUrl: string,
    private model: string,
    private enabled: boolean,
    private bus: EventBus,
    private actor: string,
  ) {}

  /** Decide a free-text exploration action from the current scene. */
  async decideAction(scene: string): Promise<string> {
    if (this.enabled && this.failCount < 3) {
      const t0 = Date.now();
      try {
        const res = await fetch(`${this.ollamaUrl}/api/chat`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            model: this.model,
            stream: false,
            options: { temperature: 0.9, num_predict: 60 },
            messages: [
              { role: 'system', content: SYSTEM_PROMPT(this.persona) },
              ...this.history.slice(-6).map((h) => ({ role: 'assistant' as const, content: h })),
              { role: 'user', content: `The DM says: ${scene.slice(0, 1200)}\n\nWhat do you do?` },
            ],
          }),
          signal: AbortSignal.timeout(90_000),
        });
        if (!res.ok) throw new Error(`ollama HTTP ${res.status}`);
        const data = (await res.json()) as { message?: { content?: string } };
        let action = (data.message?.content || '').trim().replace(/^["']|["']$/g, '').split('\n')[0];
        if (!action) throw new Error('empty LLM action');
        if (action.length > 200) action = action.slice(0, 200);
        this.history.push(action);
        this.bus.emit(this.actor, 'brain', { source: 'llm', ms: Date.now() - t0, action });
        return action;
      } catch (err) {
        this.failCount++;
        this.bus.emit(this.actor, 'brain', { source: 'llm-failed', ms: Date.now() - t0, error: String(err) });
      }
    }
    const action = this.persona.playbook[this.playbookIdx++ % this.persona.playbook.length];
    this.bus.emit(this.actor, 'brain', { source: 'playbook', action });
    return action;
  }

  /** Pick a combat quick action — weighted like a real player. */
  decideCombatAction(hpFraction: number): 'Attack' | 'Dodge' | 'Use Potion' {
    if (hpFraction < 0.3 && Math.random() < 0.7) return 'Use Potion';
    if (Math.random() < 0.15) return 'Dodge';
    return 'Attack';
  }
}
