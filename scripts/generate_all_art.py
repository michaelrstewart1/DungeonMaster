"""Generate all game art using Pollinations.ai free API — races, classes, backgrounds, landscapes."""
import urllib.request
import urllib.parse
import os
import time

BASE_DIR = os.path.join(os.path.dirname(__file__), '..', 'frontend', 'public', 'art')

RACES = [
    ("human", "dark fantasy portrait of a human adventurer, determined eyes, chainmail, torch-lit dungeon, dramatic lighting, digital painting, D&D style"),
    ("elf", "dark fantasy portrait of an elf, long pointed ears, silver hair, piercing green eyes, elegant elven armor, moonlit forest, dramatic lighting, digital painting"),
    ("dwarf", "dark fantasy portrait of a dwarf, thick braided beard, stone crown, heavy plate armor, glowing forge behind, dramatic lighting, digital painting, D&D style"),
    ("halfling", "dark fantasy portrait of a halfling, curly brown hair, warm smile, leather vest, rolling green hills, dramatic lighting, digital painting, D&D style"),
    ("gnome", "dark fantasy portrait of a gnome, wild white hair, goggles on forehead, tinkerer's apron, glowing inventions, dramatic lighting, digital painting, D&D style"),
    ("half-elf", "dark fantasy portrait of a half-elf, elegant features, one pointed ear visible, dual heritage, forest and city blend background, dramatic lighting, digital painting"),
    ("half-orc", "dark fantasy portrait of a half-orc, green-grey skin, small tusks, fierce but noble eyes, tribal markings, dramatic lighting, digital painting, D&D style"),
    ("tiefling", "dark fantasy portrait of a tiefling, crimson skin, curved horns, glowing amber eyes, dark robes, infernal energy wisps, dramatic lighting, digital painting"),
    ("dragonborn", "dark fantasy portrait of a dragonborn, golden scales, draconic horns, proud warrior stance, breath weapon glow, dramatic lighting, digital painting, D&D style"),
]

CLASSES = [
    ("barbarian", "dark fantasy portrait of a barbarian warrior, massive muscles, tribal war paint, fur cloak, great axe, berserker rage red eyes, dramatic lighting, digital painting"),
    ("bard", "dark fantasy portrait of a bard, elegant clothes, lute in hand, magical music notes floating, charismatic smile, tavern background, dramatic lighting, digital painting"),
    ("cleric", "dark fantasy portrait of a cleric, holy vestments, glowing divine symbol, healing light, plate armor, holy scripture, dramatic lighting, digital painting, D&D style"),
    ("druid", "dark fantasy portrait of a druid, leaf-woven robes, glowing green eyes, wild hair with vines, wolf companion, ancient forest, dramatic lighting, digital painting"),
    ("fighter", "dark fantasy portrait of a fighter, full plate armor, sword and shield, battle-scarred, stoic expression, castle battlements, dramatic lighting, digital painting"),
    ("monk", "dark fantasy portrait of a monk, simple robes, martial arts stance, ki energy glowing around fists, monastery background, serene, dramatic lighting, digital painting"),
    ("paladin", "dark fantasy portrait of a paladin, shining plate armor, holy sword with divine glow, cape flowing, righteous aura, cathedral, dramatic lighting, digital painting"),
    ("ranger", "dark fantasy portrait of a ranger, hooded cloak, longbow, companion hawk on shoulder, forest shadows, tracking pose, dramatic lighting, digital painting, D&D style"),
    ("rogue", "dark fantasy portrait of a rogue, leather armor, hidden daggers, shadowy hood, one eye visible, dark alley, dramatic lighting, digital painting, D&D style"),
    ("sorcerer", "dark fantasy portrait of a sorcerer, wild magic crackling around hands, glowing eyes, arcane tattoos, flowing robes, raw magical power, dramatic lighting, digital painting"),
    ("warlock", "dark fantasy portrait of a warlock, dark pact sigils glowing, eldritch blast in hand, patron's eye in background, ominous robes, dramatic lighting, digital painting"),
    ("wizard", "dark fantasy portrait of a wizard, long beard, pointed hat, ancient spellbook, arcane circles floating, tower study, dramatic lighting, digital painting, D&D style"),
]

BACKGROUNDS = [
    ("acolyte", "dark fantasy scene of a temple interior, candlelit altar, holy texts, incense smoke, stained glass window, dramatic lighting, digital painting, D&D style"),
    ("charlatan", "dark fantasy scene of a shadowy marketplace, false identities, disguise kit, forged documents, deceptive smile, dramatic lighting, digital painting"),
    ("criminal", "dark fantasy scene of a thieves guild hideout, lockpicks, stolen goods, shadowy figures, wanted posters, dramatic lighting, digital painting, D&D style"),
    ("entertainer", "dark fantasy scene of a grand performance hall, stage lights, audience silhouettes, musical instruments, performer spotlight, dramatic lighting, digital painting"),
    ("folk-hero", "dark fantasy scene of a village hero, peasant crowd cheering, rustic farmland, humble origins, rising sun, dramatic lighting, digital painting, D&D style"),
    ("guild-artisan", "dark fantasy scene of a master craftsman workshop, anvil and forge, fine tools, masterwork creation glowing, dramatic lighting, digital painting"),
    ("hermit", "dark fantasy scene of a secluded hermit cave, meditation candles, ancient scrolls, crystal formations, mystical solitude, dramatic lighting, digital painting"),
    ("noble", "dark fantasy scene of a grand noble court, throne room, velvet curtains, golden crown, heraldic banners, dramatic lighting, digital painting, D&D style"),
    ("sage", "dark fantasy scene of an ancient library, towering bookshelves, floating tomes, arcane globe, candlelit study desk, dramatic lighting, digital painting"),
    ("sailor", "dark fantasy scene of a ship on stormy seas, lightning, massive waves, pirate flag, salt-worn deck, dramatic lighting, digital painting, D&D style"),
    ("soldier", "dark fantasy scene of a military encampment, war tents, battle standards, weapon racks, campfire, veteran soldiers, dramatic lighting, digital painting"),
    ("urchin", "dark fantasy scene of dark city streets, orphan hideout, rooftop view, stolen bread, stray cat companion, moonlit alleys, dramatic lighting, digital painting"),
]

LANDSCAPES = [
    ("dragon-peak", "epic fantasy landscape of a massive mountain peak with a dragon silhouette, volcanic glow, dark storm clouds, cinematic wide shot, dramatic lighting, digital painting"),
    ("ancient-citadel", "epic fantasy landscape of an ancient floating citadel, crumbling towers, magical bridges, starlit sky, cinematic wide shot, dramatic lighting, digital painting"),
    ("enchanted-forest", "epic fantasy landscape of a deep enchanted forest, bioluminescent mushrooms, ancient trees, fairy lights, mist, cinematic wide shot, dramatic lighting, digital painting"),
    ("volcanic-wasteland", "epic fantasy landscape of a volcanic wasteland, rivers of lava, obsidian spires, ash clouds, hellish glow, cinematic wide shot, dramatic lighting, digital painting"),
    ("frozen-throne", "epic fantasy landscape of an ice kingdom, frozen throne on glacier, aurora borealis, ice crystals, blizzard, cinematic wide shot, dramatic lighting, digital painting"),
    ("abyssal-depths", "epic fantasy landscape of an underwater abyss, sunken ruins, bioluminescent creatures, dark ocean depths, ancient leviathan, cinematic wide shot, dramatic lighting"),
    ("celestial-sanctum", "epic fantasy landscape of a celestial realm, golden clouds, divine architecture, angelic light, starfield, cinematic wide shot, dramatic lighting, digital painting"),
    ("stormy-seas", "epic fantasy landscape of a raging ocean storm, massive ship battling waves, lightning strikes, kraken tentacles, cinematic wide shot, dramatic lighting, digital painting"),
]

CATEGORIES = [
    ("races", RACES, 512, 512),
    ("classes", CLASSES, 512, 512),
    ("backgrounds", BACKGROUNDS, 512, 512),
    ("landscapes", LANDSCAPES, 1024, 512),
]


def download_image(filepath, prompt, width, height, seed, retries=3):
    if os.path.exists(filepath) and os.path.getsize(filepath) > 10000:
        print(f"    ✓ Already exists ({os.path.getsize(filepath):,} bytes)")
        return True

    encoded = urllib.parse.quote(prompt)
    url = f"https://image.pollinations.ai/prompt/{encoded}?width={width}&height={height}&seed={seed}&nologo=true"

    for attempt in range(1, retries + 1):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=180) as response:
                data = response.read()
                if len(data) < 5000:
                    print(f"    ⚠ Too small ({len(data)} bytes), retrying...")
                    time.sleep(5)
                    continue
                with open(filepath, 'wb') as f:
                    f.write(data)
                print(f"    ✓ Saved ({len(data):,} bytes)")
                return True
        except Exception as e:
            print(f"    ✗ Error: {e}")
            if attempt < retries:
                wait = 10 * attempt
                print(f"    Waiting {wait}s...")
                time.sleep(wait)
    return False


def main():
    total = sum(len(items) for _, items, _, _ in CATEGORIES)
    print(f"Generating {total} art assets via Pollinations.ai\n")

    overall = 0
    for cat_name, items, w, h in CATEGORIES:
        cat_dir = os.path.join(BASE_DIR, cat_name)
        os.makedirs(cat_dir, exist_ok=True)
        print(f"\n{'='*50}")
        print(f"  {cat_name.upper()} ({len(items)} images, {w}x{h})")
        print(f"{'='*50}")

        for i, (item_id, prompt) in enumerate(items):
            overall += 1
            print(f"  [{overall}/{total}] {item_id}")
            filepath = os.path.join(cat_dir, f"{item_id}.jpg")
            seed = abs(hash(f"{cat_name}-{item_id}")) % 99999
            download_image(filepath, prompt, w, h, seed)
            if i < len(items) - 1:
                time.sleep(2)

    print(f"\n{'='*50}")
    print("Done! Generated files:")
    for cat_name, _, _, _ in CATEGORIES:
        cat_dir = os.path.join(BASE_DIR, cat_name)
        files = sorted(os.listdir(cat_dir))
        print(f"\n  {cat_name}/")
        for f in files:
            size = os.path.getsize(os.path.join(cat_dir, f))
            print(f"    {f}: {size:,} bytes")


if __name__ == '__main__':
    main()
