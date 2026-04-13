/**
 * AI Dungeon Master Bridge — Foundry VTT Module
 *
 * Connects the AI DM backend (FastAPI) to Foundry VTT via WebSocket.
 * The AI DM gets full, real-time access to everything on the table:
 *   READ  — HP, positions, conditions, initiative, dice rolls, chat, fog, scenes
 *   WRITE — narration, token moves, conditions, HP updates, new tokens, scene changes
 */

const MODULE_ID = "ai-dm-bridge";

/* ─────────────────────────────────────────────────────────────────────────── */
/*  Settings registration                                                       */
/* ─────────────────────────────────────────────────────────────────────────── */

Hooks.once("init", () => {
  game.settings.register(MODULE_ID, "backendUrl", {
    name: "Backend URL",
    hint: 'URL of the AI DM backend, e.g. "http://192.168.1.94:8000"',
    scope: "world",
    config: true,
    type: String,
    default: "http://localhost:8000",
  });

  game.settings.register(MODULE_ID, "sessionId", {
    name: "Session ID",
    hint: "The game session ID returned by the AI DM backend (POST /api/game/sessions).",
    scope: "world",
    config: true,
    type: String,
    default: "",
  });

  game.settings.register(MODULE_ID, "enableVoice", {
    name: "Enable Voice Narration",
    hint: "Play the AI DM's wizard voice through this browser when narration arrives.",
    scope: "client",
    config: true,
    type: Boolean,
    default: true,
  });

  game.settings.register(MODULE_ID, "autoGreeting", {
    name: "Session Greeting on Load",
    hint: "Fetch and display the DM greeting/recap when you first open this world.",
    scope: "world",
    config: true,
    type: Boolean,
    default: true,
  });
});

/* ─────────────────────────────────────────────────────────────────────────── */
/*  Core Bridge class                                                           */
/* ─────────────────────────────────────────────────────────────────────────── */

class AIDMBridge {
  constructor() {
    this.socket = null;
    this._reconnectTimer = null;
    this._audioCtx = null;
  }

  get backendUrl() {
    return game.settings.get(MODULE_ID, "backendUrl").replace(/\/$/, "");
  }

  get sessionId() {
    return game.settings.get(MODULE_ID, "sessionId");
  }

  /* ── WebSocket connection ── */

  connect() {
    if (!this.sessionId) {
      console.warn(`[${MODULE_ID}] No Session ID configured — bridge inactive.`);
      return;
    }

    const wsUrl = this.backendUrl.replace(/^http/, "ws") + `/ws/game/${this.sessionId}`;
    console.log(`[${MODULE_ID}] Connecting to ${wsUrl}`);

    this.socket = new WebSocket(wsUrl);

    this.socket.onopen = () => {
      console.log(`[${MODULE_ID}] Connected ✓`);
      ui.notifications.info("AI DM Bridge connected!");
      clearTimeout(this._reconnectTimer);
    };

    this.socket.onmessage = (evt) => {
      try {
        this._handleBackendMessage(JSON.parse(evt.data));
      } catch (e) {
        console.error(`[${MODULE_ID}] Bad message:`, evt.data, e);
      }
    };

    this.socket.onclose = () => {
      console.warn(`[${MODULE_ID}] Disconnected — retrying in 5 s…`);
      this._reconnectTimer = setTimeout(() => this.connect(), 5000);
    };

    this.socket.onerror = (err) => {
      console.error(`[${MODULE_ID}] WebSocket error:`, err);
    };
  }

  sendToBackend(data) {
    if (this.socket?.readyState === WebSocket.OPEN) {
      this.socket.send(JSON.stringify(data));
    }
  }

  /* ── Foundry event hooks → backend ── */

  registerHooks() {
    /* Combat turn changes */
    Hooks.on("combatTurn", (combat) => {
      this.sendToBackend({
        type: "combat_turn",
        round: combat.round,
        turn: combat.turn,
        current_combatant: combat.current?.name ?? null,
        initiative_order: combat.turns.map((t) => ({
          name: t.name,
          initiative: t.initiative,
          hp: t.actor?.system?.attributes?.hp?.value ?? null,
          max_hp: t.actor?.system?.attributes?.hp?.max ?? null,
          conditions: t.actor?.statuses ? [...t.actor.statuses] : [],
        })),
      });
    });

    /* Combat round changes */
    Hooks.on("combatRound", (combat) => {
      this.sendToBackend({
        type: "combat_round",
        round: combat.round,
        initiative_order: combat.turns.map((t) => t.name),
      });
    });

    /* HP / actor updates */
    Hooks.on("updateActor", (actor, updateData) => {
      if (updateData?.system?.attributes?.hp) {
        this.sendToBackend({
          type: "hp_update",
          actor_name: actor.name,
          hp: actor.system.attributes.hp.value,
          max_hp: actor.system.attributes.hp.max,
          temp_hp: actor.system.attributes.hp.temp ?? 0,
        });
      }
    });

    /* Token movement */
    Hooks.on("updateToken", (token, updateData) => {
      if (updateData.x !== undefined || updateData.y !== undefined) {
        this.sendToBackend({
          type: "token_moved",
          token_name: token.name,
          x: token.x,
          y: token.y,
          new_x: updateData.x ?? token.x,
          new_y: updateData.y ?? token.y,
        });
      }
    });

    /* Dice rolls */
    Hooks.on("createChatMessage", (message) => {
      if (message.isRoll) {
        this.sendToBackend({
          type: "dice_roll",
          speaker: message.speaker?.alias ?? "Unknown",
          flavor: message.flavor ?? "",
          total: message.rolls?.[0]?.total ?? null,
          formula: message.rolls?.[0]?.formula ?? null,
          is_critical: message.rolls?.[0]?.isCritical ?? false,
          is_fumble: message.rolls?.[0]?.isFumble ?? false,
        });
        return; // don't re-send as player_chat
      }

      // Player chat (skip DM messages to avoid loops)
      if (message.speaker?.alias !== "Dungeon Master") {
        this.sendToBackend({
          type: "player_chat",
          message: message.content,
          speaker: message.speaker?.alias ?? "Unknown",
        });
      }
    });

    /* Scene activation */
    Hooks.on("canvasReady", (canvas) => {
      this.sendToBackend({
        type: "scene_loaded",
        scene_name: canvas.scene?.name ?? "Unknown",
        scene_id: canvas.scene?.id ?? null,
      });
    });
  }

  /* ── Backend commands → Foundry ── */

  async _handleBackendMessage(data) {
    switch (data.type) {

      /* Post narration to chat as the Dungeon Master */
      case "narration": {
        await ChatMessage.create({
          speaker: { alias: "Dungeon Master" },
          content: `<p><em>${data.text}</em></p>`,
          type: CONST.CHAT_MESSAGE_STYLES?.OTHER ?? 0,
        });
        if (game.settings.get(MODULE_ID, "enableVoice") && data.audio_url) {
          this._playAudioUrl(data.audio_url);
        }
        break;
      }

      /* Move a token */
      case "move_token": {
        const token = canvas.tokens?.placeables?.find((t) => t.name === data.token_name);
        if (token) {
          await token.document.update({ x: data.x, y: data.y });
        } else {
          console.warn(`[${MODULE_ID}] Token not found: ${data.token_name}`);
        }
        break;
      }

      /* Apply a condition / status effect */
      case "apply_condition": {
        const actor = game.actors?.find((a) => a.name === data.actor_name);
        if (actor) await actor.toggleStatusEffect(data.condition, { active: true });
        break;
      }

      /* Remove a condition */
      case "remove_condition": {
        const actor = game.actors?.find((a) => a.name === data.actor_name);
        if (actor) await actor.toggleStatusEffect(data.condition, { active: false });
        break;
      }

      /* Set HP directly */
      case "update_hp": {
        const actor = game.actors?.find((a) => a.name === data.actor_name);
        if (actor) {
          await actor.update({ "system.attributes.hp.value": data.new_hp });
        }
        break;
      }

      /* Spawn a new NPC token on the active scene */
      case "create_token": {
        const scene = game.scenes?.active;
        if (scene) {
          await scene.createEmbeddedDocuments("Token", [data.token_data]);
        }
        break;
      }

      /* Remove a defeated token */
      case "delete_token": {
        const token = canvas.tokens?.placeables?.find((t) => t.name === data.token_name);
        if (token) await token.document.delete();
        break;
      }

      /* Switch to a different scene */
      case "change_scene": {
        const scene = game.scenes?.find((s) => s.name === data.scene_name);
        if (scene) await scene.activate();
        break;
      }

      /* Reveal fog-of-war tiles */
      case "reveal_fog": {
        if (canvas.scene && data.positions) {
          // data.positions: [{x, y}, ...]
          await canvas.scene.update({ fogExploration: true });
          // Foundry handles sight updates automatically on token move;
          // for manual reveals you'd use FogExploration documents
        }
        break;
      }

      /* Play ambient audio */
      case "play_audio": {
        AudioHelper.play({ src: data.src, volume: data.volume ?? 0.8, loop: data.loop ?? false }, true);
        break;
      }

      /* Show an image handout to all players */
      case "show_image": {
        new ImagePopout(data.src, { title: data.title ?? "Handout", shareable: true }).render(true).share();
        break;
      }

      /* Create or update a journal entry */
      case "update_journal": {
        let entry = game.journal?.find((j) => j.name === data.title);
        if (entry) {
          const page = entry.pages.find((p) => p.name === data.title) ?? entry.pages.contents[0];
          if (page) await page.update({ "text.content": data.content });
        } else {
          await JournalEntry.create({
            name: data.title,
            pages: [{ name: data.title, type: "text", text: { content: data.content } }],
          });
        }
        break;
      }

      default:
        console.log(`[${MODULE_ID}] Unknown message type: ${data.type}`, data);
    }
  }

  /* ── Audio playback for TTS narration ── */

  _playAudioUrl(url) {
    const audio = new Audio(url);
    audio.volume = 0.9;
    audio.play().catch((e) => console.warn(`[${MODULE_ID}] Audio play failed:`, e));
  }

  /* ── REST helpers (used for greeting, world gen, etc.) ── */

  async fetchGreeting() {
    const sid = this.sessionId;
    if (!sid) return null;
    const res = await fetch(`${this.backendUrl}/api/game/sessions/${sid}/greeting`);
    if (!res.ok) return null;
    const data = await res.json();
    return data.greeting ?? null;
  }
}

/* ─────────────────────────────────────────────────────────────────────────── */
/*  Module entry point                                                          */
/* ─────────────────────────────────────────────────────────────────────────── */

Hooks.once("ready", async () => {
  // Only the GM runs the bridge
  if (!game.user?.isGM) return;

  const bridge = new AIDMBridge();
  bridge.registerHooks();
  bridge.connect();

  // Expose on game object for console debugging
  game.aiDMBridge = bridge;

  // Optional: auto-fetch session greeting and post it to chat
  if (game.settings.get(MODULE_ID, "autoGreeting")) {
    const greeting = await bridge.fetchGreeting();
    if (greeting) {
      await ChatMessage.create({
        speaker: { alias: "Dungeon Master" },
        content: `<p><em>${greeting}</em></p>`,
        type: CONST.CHAT_MESSAGE_STYLES?.OTHER ?? 0,
      });
    }
  }

  console.log(`[${MODULE_ID}] AI DM Bridge ready.`);
});
