/**
 * Multiplayer Simulation — screenshots every view at real device sizes
 * so the user can see what the table-top experience looks like before buying hardware.
 *
 * TV:    1920×1080 (DM Display)
 * Phone: 390×844  (iPhone 14 — Player View, Join Page)
 * Laptop: 1280×800 (Lobby — host's laptop)
 */
import { test, expect, type Page } from '@playwright/test';

const MOCK_SESSION_ID = 'sim-session-001';
const MOCK_CAMPAIGN_ID = 'sim-campaign-001';
const ROOM_CODE = 'DRAK';

// Realistic party — the user's family
const MOCK_CHARACTERS = [
  {
    id: 'char-kit', name: 'Lyra Nightwhisper', race: 'Half-Elf', class_name: 'Ranger',
    level: 5, hp: 38, max_hp: 42, ac: 15, subclass: 'Gloom Stalker',
    strength: 12, dexterity: 18, constitution: 14, intelligence: 10, wisdom: 16, charisma: 13,
    skills: ['Stealth', 'Perception', 'Survival', 'Nature', 'Animal Handling'],
    equipment: ['Longbow +1', 'Shortsword', 'Studded Leather Armor', 'Explorer\'s Pack', 'Rope of Climbing'],
    spells_known: ['Hunter\'s Mark', 'Cure Wounds', 'Pass Without Trace', 'Spike Growth'],
    portrait_url: '/portraits/lyra.jpg',
  },
  {
    id: 'char-cohen', name: 'Thorin Ironforge', race: 'Dwarf', class_name: 'Paladin',
    level: 5, hp: 52, max_hp: 52, ac: 18, subclass: 'Oath of Devotion',
    strength: 18, dexterity: 10, constitution: 16, intelligence: 8, wisdom: 12, charisma: 16,
    skills: ['Athletics', 'Religion', 'Persuasion', 'Intimidation'],
    equipment: ['Warhammer +1', 'Shield of Faith', 'Chain Mail', 'Holy Symbol', 'Javelins (5)'],
    spells_known: ['Shield of Faith', 'Thunderous Smite', 'Cure Wounds', 'Bless'],
    portrait_url: '/portraits/thorin.jpg',
  },
  {
    id: 'char-brody', name: 'Zephyr Stormcaller', race: 'Tiefling', class_name: 'Sorcerer',
    level: 5, hp: 22, max_hp: 30, ac: 13, subclass: 'Draconic Bloodline',
    strength: 8, dexterity: 14, constitution: 12, intelligence: 14, wisdom: 10, charisma: 20,
    skills: ['Arcana', 'Deception', 'Insight', 'Persuasion'],
    equipment: ['Arcane Focus (crystal)', 'Dagger', 'Component Pouch', 'Scholar\'s Pack'],
    spells_known: ['Fireball', 'Shield', 'Misty Step', 'Scorching Ray', 'Mage Armor', 'Chromatic Orb', 'Prestidigitation', 'Fire Bolt'],
    portrait_url: '/portraits/zephyr.jpg',
  },
  {
    id: 'char-michael', name: 'Grimshaw the Unbroken', race: 'Human', class_name: 'Fighter',
    level: 5, hp: 44, max_hp: 50, ac: 17, subclass: 'Battle Master',
    strength: 20, dexterity: 14, constitution: 16, intelligence: 12, wisdom: 10, charisma: 8,
    skills: ['Athletics', 'Perception', 'Survival', 'Intimidation'],
    equipment: ['Greatsword +1', 'Longbow', 'Splint Armor', 'Explorer\'s Pack', 'Handaxes (2)'],
    spells_known: [],
    portrait_url: '/portraits/grimshaw.jpg',
  },
];

const MOCK_GAME_STATE = {
  session_id: MOCK_SESSION_ID,
  campaign_id: MOCK_CAMPAIGN_ID,
  phase: 'exploration',
  current_scene: 'You descend the crumbling stone steps into the Drakkenhold crypts. Torchlight flickers against walls carved with ancient dwarven runes — warnings etched by hands long turned to dust. The air is thick with the scent of damp earth and something else… sulfur. Ahead, the passage splits: a narrow corridor stretches left into darkness, while a wider hall opens to the right, its floor littered with shattered bones.',
  turn_number: 7,
  combat_state: null,
};

const MOCK_GAME_STATE_COMBAT = {
  ...MOCK_GAME_STATE,
  phase: 'combat',
  current_scene: 'A bone-chilling screech tears through the crypt as three skeletal warriors lurch from the shadows! Their rusted blades catch the torchlight as they advance. Thorin raises his warhammer, divine light surging through the runes. "Moradin guide my hand!" Roll initiative!',
  combat_state: {
    initiative_order: ['Zephyr Stormcaller', 'Skeleton Warrior', 'Lyra Nightwhisper', 'Thorin Ironforge', 'Skeleton Archer', 'Grimshaw the Unbroken', 'Skeleton Captain'],
    current_turn_index: 2,
    round_number: 2,
  },
};

const MOCK_PLAYERS = [
  { id: 'p1', name: 'Kit', characterId: 'char-kit', isReady: true },
  { id: 'p2', name: 'Cohen', characterId: 'char-cohen', isReady: true },
  { id: 'p3', name: 'Brody', characterId: 'char-brody', isReady: true },
  { id: 'p4', name: 'Michael', characterId: 'char-michael', isReady: false },
];

const MOCK_AVATAR = {
  expression: 'dramatic',
  is_speaking: true,
  mouth_amplitude: 0.7,
  gaze: { x: 0.2, y: -0.1 },
};

async function mockAPIs(page: Page, gameState = MOCK_GAME_STATE) {
  // Mock all API calls with realistic data
  await page.route('**/api/game/sessions/*/state', (route) => {
    route.fulfill({ json: gameState });
  });
  await page.route('**/api/game/sessions/*/room-code', (route) => {
    route.fulfill({ json: { room_code: ROOM_CODE, session_id: MOCK_SESSION_ID } });
  });
  await page.route('**/api/game/sessions/*/players', (route) => {
    route.fulfill({ json: { players: MOCK_PLAYERS } });
  });
  await page.route('**/api/characters?campaign_id=*', (route) => {
    route.fulfill({ json: MOCK_CHARACTERS });
  });
  await page.route('**/api/characters/char-kit', (route) => {
    route.fulfill({ json: MOCK_CHARACTERS[0] });
  });
  await page.route('**/api/characters/char-cohen', (route) => {
    route.fulfill({ json: MOCK_CHARACTERS[1] });
  });
  await page.route('**/api/characters/char-brody', (route) => {
    route.fulfill({ json: MOCK_CHARACTERS[2] });
  });
  await page.route('**/api/characters/char-michael', (route) => {
    route.fulfill({ json: MOCK_CHARACTERS[3] });
  });
  await page.route('**/api/avatar/*', (route) => {
    route.fulfill({ json: MOCK_AVATAR });
  });
  // Block WebSocket so pages don't error
  await page.route('**/ws/**', (route) => route.abort());
  await page.route('**/api/game/join', (route) => {
    route.fulfill({ json: { session_id: MOCK_SESSION_ID, player_id: 'p1', campaign_id: MOCK_CAMPAIGN_ID } });
  });
}

test.describe('Multiplayer Simulation Screenshots', () => {

  // ===== 1. JOIN PAGE — Phone (390×844) =====
  test('📱 Join Page — what players see on their phone', async ({ browser }) => {
    const context = await browser.newContext({ viewport: { width: 390, height: 844 } });
    const page = await context.newPage();
    await mockAPIs(page);

    await page.goto('/join');
    await page.waitForSelector('.join-game-card');
    // Fill in realistic data
    await page.fill('input[placeholder*="Cohen"]', 'Cohen');
    await page.fill('input[placeholder="ABCD"]', ROOM_CODE);
    await page.screenshot({ path: 'test-results/sim-01-join-phone.png', fullPage: true });
    await context.close();
  });

  // ===== 2. LOBBY — Laptop (1280×800) =====
  test('💻 Lobby — host laptop showing room code & players', async ({ browser }) => {
    const context = await browser.newContext({ viewport: { width: 1280, height: 800 } });
    const page = await context.newPage();
    await mockAPIs(page);

    await page.goto(`/lobby/${MOCK_SESSION_ID}`);
    await page.waitForSelector('.lobby-room-code');
    await page.waitForTimeout(300);
    await page.screenshot({ path: 'test-results/sim-02-lobby-laptop.png', fullPage: true });
    await context.close();
  });

  // ===== 3. PLAYER VIEW (Play tab) — Phone =====
  test('📱 Player View (Play tab) — Kit\'s phone during exploration', async ({ browser }) => {
    const context = await browser.newContext({
      viewport: { width: 390, height: 844 },
      storageState: undefined,
    });
    const page = await context.newPage();

    // Set sessionStorage before navigating
    await page.goto('/join');
    await page.evaluate(() => {
      sessionStorage.setItem('playerName', 'Kit');
      sessionStorage.setItem('playerId', 'p1');
      sessionStorage.setItem('characterId', 'char-kit');
      sessionStorage.setItem('sessionId', 'sim-session-001');
    });

    await mockAPIs(page);
    await page.goto(`/play/${MOCK_SESSION_ID}`);
    await page.waitForSelector('.player-view');
    await page.waitForTimeout(500);

    // Inject some narrative entries to simulate a game in progress
    await page.evaluate(() => {
      const feed = document.querySelector('.pv-narrative-feed');
      if (!feed) return;
      const entries = [
        { type: 'narration', text: 'The ancient door creaks open, revealing a chamber filled with an eerie blue glow. Strange runes pulse along the walls in a rhythmic pattern.' },
        { type: 'action', sender: 'Thorin', text: 'I hold up my holy symbol and move forward cautiously, checking for traps.' },
        { type: 'narration', text: 'Thorin\'s holy symbol glows with a warm golden light. The runes seem to react, their pulsing quickening. No traps detected, but something stirs in the darkness beyond.' },
        { type: 'action', sender: 'Zephyr', text: 'I cast Detect Magic to identify the source of the glow.' },
        { type: 'narration', text: 'Zephyr\'s eyes flash with arcane sight. The blue glow emanates from a crystal embedded in a stone pedestal at the chamber\'s center — radiating strong evocation and necromancy magic.' },
        { type: 'chat', sender: 'Cohen', text: 'Should we touch it? 😬' },
        { type: 'chat', sender: 'Kit', text: 'Absolutely not, let me check for traps first' },
      ];
      feed.innerHTML = '';
      entries.forEach((e) => {
        const div = document.createElement('div');
        div.className = `pv-narrative-entry pv-entry-${e.type}`;
        if (e.sender) {
          const sp = document.createElement('span');
          sp.className = 'pv-entry-sender';
          sp.textContent = e.sender + ': ';
          div.appendChild(sp);
        }
        const txt = document.createElement('span');
        txt.className = 'pv-entry-text';
        txt.textContent = e.text;
        div.appendChild(txt);
        feed.appendChild(div);
      });
    });

    await page.screenshot({ path: 'test-results/sim-03-player-play-phone.png', fullPage: false });
    await context.close();
  });

  // ===== 4. PLAYER VIEW (Sheet tab) — Phone =====
  test('📱 Player View (Sheet tab) — character sheet on phone', async ({ browser }) => {
    const context = await browser.newContext({ viewport: { width: 390, height: 844 } });
    const page = await context.newPage();

    await page.goto('/join');
    await page.evaluate(() => {
      sessionStorage.setItem('playerName', 'Kit');
      sessionStorage.setItem('playerId', 'p1');
      sessionStorage.setItem('characterId', 'char-kit');
    });

    await mockAPIs(page);
    await page.goto(`/play/${MOCK_SESSION_ID}`);
    await page.waitForSelector('.player-view');
    await page.waitForTimeout(500);

    // Switch to sheet tab
    await page.click('button:has-text("Sheet")');
    await page.waitForTimeout(300);
    await page.screenshot({ path: 'test-results/sim-04-player-sheet-phone.png', fullPage: true });
    await context.close();
  });

  // ===== 5. DM DISPLAY (Exploration) — TV 1920×1080 =====
  test('📺 DM Display (Exploration) — TV at head of table', async ({ browser }) => {
    const context = await browser.newContext({ viewport: { width: 1920, height: 1080 } });
    const page = await context.newPage();
    await mockAPIs(page, MOCK_GAME_STATE);

    await page.goto(`/dm/${MOCK_SESSION_ID}`);
    await page.waitForSelector('.dm-display');
    await page.waitForTimeout(800);
    await page.screenshot({ path: 'test-results/sim-05-dm-display-exploration-tv.png', fullPage: false });
    await context.close();
  });

  // ===== 6. DM DISPLAY (Combat) — TV 1920×1080 =====
  test('📺 DM Display (Combat) — initiative tracker active', async ({ browser }) => {
    const context = await browser.newContext({ viewport: { width: 1920, height: 1080 } });
    const page = await context.newPage();
    await mockAPIs(page, MOCK_GAME_STATE_COMBAT);

    await page.goto(`/dm/${MOCK_SESSION_ID}`);
    await page.waitForSelector('.dm-display');
    await page.waitForTimeout(800);
    await page.screenshot({ path: 'test-results/sim-06-dm-display-combat-tv.png', fullPage: false });
    await context.close();
  });

  // ===== 7. DM DISPLAY — TV with speaking avatar =====
  test('📺 DM Display — speaking animation & narration', async ({ browser }) => {
    const context = await browser.newContext({ viewport: { width: 1920, height: 1080 } });
    const page = await context.newPage();

    // Avatar is actively speaking with dramatic expression
    const speakingAvatar = {
      expression: 'dramatic',
      is_speaking: true,
      mouth_amplitude: 0.85,
      gaze: { x: 0, y: 0 },
    };
    await page.route('**/api/avatar/*', (route) => route.fulfill({ json: speakingAvatar }));
    await mockAPIs(page, {
      ...MOCK_GAME_STATE,
      current_scene: 'From the shadows emerges a figure cloaked in writhing darkness. The Lich Lord Vexarion raises a skeletal hand, and the temperature plummets. Ice crystals form on your armor as his hollow voice echoes through the crypt: "Foolish mortals... you dare disturb my slumber? Your souls shall fuel my rebirth!"',
    });
    // Re-override avatar since mockAPIs sets it too
    await page.route('**/api/avatar/*', (route) => route.fulfill({ json: speakingAvatar }));

    await page.goto(`/dm/${MOCK_SESSION_ID}`);
    await page.waitForSelector('.dm-display');
    await page.waitForTimeout(800);
    await page.screenshot({ path: 'test-results/sim-07-dm-display-speaking-tv.png', fullPage: false });
    await context.close();
  });

  // ===== 8. COMPOSITE: Table Layout Diagram =====
  test('🪑 Table Layout — annotated diagram of physical setup', async ({ browser }) => {
    const context = await browser.newContext({ viewport: { width: 1200, height: 900 } });
    const page = await context.newPage();

    // Render an HTML diagram of the physical table setup
    await page.setContent(`
      <html>
      <head>
        <style>
          * { margin: 0; padding: 0; box-sizing: border-box; }
          body {
            background: #1a1a2e;
            color: #e8d5a3;
            font-family: 'Segoe UI', sans-serif;
            display: flex;
            flex-direction: column;
            align-items: center;
            padding: 30px;
          }
          h1 { font-size: 28px; margin-bottom: 5px; color: #c9a84c; }
          .subtitle { color: #8a7a5a; margin-bottom: 25px; font-size: 14px; }
          .table-container { position: relative; width: 900px; height: 650px; }
          .table {
            position: absolute; top: 160px; left: 150px;
            width: 600px; height: 300px;
            background: linear-gradient(135deg, #3a2510 0%, #2a1a0a 100%);
            border: 4px solid #5a3a1a;
            border-radius: 20px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.6);
            display: flex; align-items: center; justify-content: center;
            flex-direction: column;
          }
          .table-label { color: #6a5a3a; font-size: 14px; text-transform: uppercase; letter-spacing: 2px; }
          .board {
            width: 180px; height: 140px;
            background: repeating-conic-gradient(#2a3a2a 0% 25%, #1a2a1a 0% 50%) 50% / 20px 20px;
            border: 2px solid #4a5a4a;
            border-radius: 4px;
            margin-top: 8px;
            display: flex; align-items: center; justify-content: center;
          }
          .board-text { color: #6a8a6a; font-size: 10px; }
          .webcam-icon {
            position: absolute; top: 130px; left: 430px;
            background: #2a2a3e; border: 2px solid #5a5a8a;
            border-radius: 8px; padding: 4px 10px;
            font-size: 12px; color: #8a8aba;
          }
          .webcam-line {
            position: absolute; top: 145px; left: 480px;
            width: 2px; height: 20px; background: #5a5a8a;
          }
          .seat {
            position: absolute;
            width: 120px; padding: 10px;
            background: #1e1e32;
            border: 2px solid #3a3a5a;
            border-radius: 12px;
            text-align: center;
            font-size: 13px;
          }
          .seat-name { font-weight: bold; color: #c9a84c; display: block; margin-bottom: 3px; }
          .seat-device { color: #7a7a9a; font-size: 11px; display: block; }
          .seat-char { color: #6a8a6a; font-size: 10px; display: block; margin-top: 2px; }
          .tv {
            position: absolute; top: 0; left: 325px;
            width: 250px; height: 140px;
            background: linear-gradient(180deg, #0a0a1e 0%, #1a1a3e 100%);
            border: 3px solid #c9a84c;
            border-radius: 8px;
            display: flex; flex-direction: column;
            align-items: center; justify-content: center;
            box-shadow: 0 0 30px rgba(201, 168, 76, 0.3);
          }
          .tv-label { color: #c9a84c; font-weight: bold; font-size: 16px; }
          .tv-sub { color: #8a7a5a; font-size: 11px; margin-top: 3px; }
          .tv-face { font-size: 36px; margin-bottom: 5px; }
          .speaker {
            position: absolute; top: 5px; left: 260px;
            background: #1e1e32; border: 2px solid #5a5a8a;
            border-radius: 8px; padding: 8px 12px;
            font-size: 12px; color: #8a8aba;
            text-align: center;
          }
          .arrow {
            position: absolute;
            color: #5a5a8a; font-size: 11px;
          }
          .legend {
            margin-top: 15px;
            display: flex; gap: 20px;
            font-size: 12px; color: #6a6a8a;
          }
          .legend-item { display: flex; align-items: center; gap: 5px; }
          .legend-dot { width: 10px; height: 10px; border-radius: 50%; }
          /* Seat positions around the table */
          .seat-top-left { top: 105px; left: 20px; }
          .seat-top-right { top: 105px; right: 20px; }
          .seat-left { top: 280px; left: 10px; }
          .seat-right { top: 280px; right: 10px; }
          .seat-bottom-left { top: 490px; left: 170px; }
          .seat-bottom-right { top: 490px; right: 170px; }
          .seat-bottom-center { top: 500px; left: 390px; }
        </style>
      </head>
      <body>
        <h1>🏰 AI Dungeon Master — Table Layout</h1>
        <div class="subtitle">How your dining table becomes a D&D command center</div>

        <div class="table-container">
          <!-- TV at head of table -->
          <div class="tv">
            <div class="tv-face">🧙</div>
            <div class="tv-label">DM Display (TV)</div>
            <div class="tv-sub">Battle map • Narration • Initiative</div>
          </div>

          <!-- Speaker -->
          <div class="speaker">🔊 Speaker<br/><span style="font-size:10px;color:#6a6a8a">TTS voice</span></div>

          <!-- Webcam -->
          <div class="webcam-icon">📷 Webcam (overhead)</div>
          <div class="webcam-line"></div>

          <!-- Table -->
          <div class="table">
            <div class="table-label">Dining Table</div>
            <div class="board">
              <div class="board-text">D&D Board<br/>& Minis</div>
            </div>
          </div>

          <!-- Seats -->
          <div class="seat seat-top-left">
            <span class="seat-name">Kit</span>
            <span class="seat-device">📱 Phone</span>
            <span class="seat-char">Lyra • Ranger 5</span>
          </div>

          <div class="seat seat-top-right">
            <span class="seat-name">Cousin</span>
            <span class="seat-device">📱 Phone</span>
            <span class="seat-char">Guest character</span>
          </div>

          <div class="seat seat-left">
            <span class="seat-name">Cohen</span>
            <span class="seat-device">📱 Phone</span>
            <span class="seat-char">Thorin • Paladin 5</span>
          </div>

          <div class="seat seat-right">
            <span class="seat-name">Brody</span>
            <span class="seat-device">📱 Phone</span>
            <span class="seat-char">Zephyr • Sorcerer 5</span>
          </div>

          <div class="seat seat-bottom-left">
            <span class="seat-name">Michael</span>
            <span class="seat-device">📱 Phone + 💻 Host</span>
            <span class="seat-char">Grimshaw • Fighter 5</span>
          </div>

          <div class="seat seat-bottom-right">
            <span class="seat-name">Extra Seat</span>
            <span class="seat-device">📱 Phone</span>
            <span class="seat-char">Drop-in player</span>
          </div>
        </div>

        <div class="legend">
          <div class="legend-item"><div class="legend-dot" style="background:#c9a84c"></div> TV — DM face, map, narration</div>
          <div class="legend-item"><div class="legend-dot" style="background:#4a8a4a"></div> Phones — character sheets, actions</div>
          <div class="legend-item"><div class="legend-dot" style="background:#5a5a8a"></div> Webcam — sees board, tracks minis</div>
          <div class="legend-item"><div class="legend-dot" style="background:#8a4a4a"></div> Speaker — DM voice (TTS)</div>
        </div>
      </body>
      </html>
    `);
    await page.screenshot({ path: 'test-results/sim-00-table-layout.png' });
    await context.close();
  });
});
