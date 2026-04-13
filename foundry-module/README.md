# AI Dungeon Master — Foundry VTT Module

This Foundry VTT module connects your copy of Foundry to the AI Dungeon Master backend, giving the AI full read/write access to your game — just like a human DM would have.

---

## What the AI DM can see (automatically)

| Data | Source |
|---|---|
| Every character's HP, max HP, temp HP | `updateActor` hook |
| Conditions on any token (Stunned, Frightened, etc.) | `updateActor` hook |
| Full initiative order every round | `combatTurn` / `combatRound` hooks |
| Token positions on the map (x, y grid coords) | `updateToken` hook |
| Every dice roll (total, formula, crit/fumble) | `createChatMessage` hook |
| All player chat messages | `createChatMessage` hook |
| Which scene / map is currently active | `canvasReady` hook |

---

## What the AI DM can do (via backend commands)

| Command | Effect |
|---|---|
| `narration` | Posts DM narration to Foundry chat as "Dungeon Master" |
| `move_token` | Moves a token to given (x, y) coordinates |
| `apply_condition` | Applies a status effect (stunned, prone, frightened…) |
| `remove_condition` | Removes a status effect |
| `update_hp` | Sets an actor's HP to a specific value |
| `create_token` | Spawns a new NPC token on the active scene |
| `delete_token` | Removes a defeated token from the map |
| `change_scene` | Activates a different scene (moves party to new map) |
| `play_audio` | Plays ambient audio for all players |
| `show_image` | Displays a full-screen image handout to all players |
| `update_journal` | Creates or updates a Journal entry (world notes, session recap) |

---

## Installation

### Step 1 — Copy module files
Copy the `foundry-module/` folder from this repo into your Foundry `Data/modules/` directory and rename it `ai-dm-bridge`:

```
FoundryVTT/Data/modules/ai-dm-bridge/
  module.json
  dm-bridge.js
  README.md
```

### Step 2 — Enable the module
1. In Foundry, open **Game Settings → Manage Modules**
2. Enable **AI Dungeon Master Bridge**
3. Save changes and reload

### Step 3 — Configure the module
1. Open **Game Settings → Configure Settings → Module Settings**
2. Set **Backend URL** to your AI DM server's LAN address, e.g. `http://192.168.1.94:8000`
3. Set **Session ID** — you get this from the backend:
   ```
   POST http://192.168.1.94:8000/api/game/sessions
   Body: {"campaign_id": "<your-campaign-id>"}
   ```
   Copy the `id` from the response.
4. Enable **Voice Narration** if you want the wizard voice played through your browser.

---

## Starting a session

### Option A — Using `start-lan.bat` (Windows host)
Double-click `start-lan.bat` in the repo root.  It will print your LAN IP address and start the backend on port 8000, accessible to everyone on the same WiFi.

### Option B — Manual
```bash
cd backend
python -m uvicorn app.main:create_app --factory --host 0.0.0.0 --port 8000
```

---

## Session greeting

When a world loads, the module automatically fetches the session greeting from the backend and posts it to chat. The AI DM will:
- Greet players in its deep wizard voice
- Recap what happened last session
- Set the scene for tonight

To save a session summary at the end of a session (so next time's recap is accurate):
```
POST http://<server>:8000/api/game/sessions/<session-id>/summary
Body: {} 
```
Leave the body empty and the AI will auto-generate the recap from the narrative history.

---

## World generation

To have the AI build a rich world for a new campaign:
```
POST http://<server>:8000/api/game/world/generate
Body: {
  "campaign_id": "<campaign-id>",
  "theme": "dark_fantasy",
  "setting": "sunken coastal empire ruled by necromancers",
  "hooks": ["the king is missing", "an ancient dragon has awakened"]
}
```

---

## Troubleshooting

- **Bridge shows "disconnected"** — check that the backend is running and the Backend URL is correct (include `http://`, not `ws://`).
- **No session greeting** — make sure Session ID is set in module settings.
- **Narration not appearing** — the AI DM needs an `OPENAI_API_KEY` in the backend's `.env` file.
