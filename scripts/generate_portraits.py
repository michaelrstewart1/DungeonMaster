"""Generate AI character portraits using Pollinations.ai free API."""
import urllib.request
import urllib.parse
import os
import time

PORTRAITS_DIR = os.path.join(os.path.dirname(__file__), '..', 'frontend', 'public', 'portraits')
os.makedirs(PORTRAITS_DIR, exist_ok=True)

# Shorter, more focused prompts work better with the API
CHARACTERS = [
    ("thorne", "dark fantasy portrait of a grizzled dwarf fighter, thick braided beard, plate armor, battleaxe, dramatic lighting, digital painting"),
    ("lyra", "dark fantasy portrait of a female elf wizard, long silver hair, glowing blue eyes, arcane robes, magic staff, dramatic lighting, digital painting"),
    ("kael", "dark fantasy portrait of a male halfling rogue, messy brown hair, leather hood, daggers, mischievous grin, dramatic lighting, digital painting"),
    ("sera", "dark fantasy portrait of a female human paladin, golden hair braid, shining plate armor, holy light, sun emblem, dramatic lighting, digital painting"),
    ("zephyr", "dark fantasy portrait of a male tiefling warlock, red skin, curved horns, glowing eyes, dark robes, eldritch energy, dramatic lighting, digital painting"),
    ("briar", "dark fantasy portrait of a female half-elf druid, auburn hair with leaves, green eyes, natural armor, forest spirit, dramatic lighting, digital painting"),
    ("grimjaw", "dark fantasy portrait of a male half-orc barbarian, green skin, tusks, tribal war paint, fur cloak, muscular, fierce, dramatic lighting, digital painting"),
    ("melody", "dark fantasy portrait of a female gnome bard, pink curly hair, bright eyes, lute, performer clothes, cheerful, dramatic lighting, digital painting"),
    ("ashara", "dark fantasy portrait of a female dragonborn cleric, golden scales, horns, holy vestments, divine light, noble, dramatic lighting, digital painting"),
    ("ren", "dark fantasy portrait of a male human monk, shaved head, calm eyes, simple robes, martial artist, serene, dramatic lighting, digital painting"),
]


def download_portrait(char_id, prompt, retries=3):
    filename = f"{char_id}.jpg"
    filepath = os.path.join(PORTRAITS_DIR, filename)

    if os.path.exists(filepath) and os.path.getsize(filepath) > 10000:
        print(f"  ✓ Already exists: {filename} ({os.path.getsize(filepath):,} bytes)")
        return True

    encoded = urllib.parse.quote(prompt)
    seed = abs(hash(char_id)) % 99999
    url = f"https://image.pollinations.ai/prompt/{encoded}?width=512&height=512&seed={seed}&nologo=true"

    for attempt in range(1, retries + 1):
        print(f"  Generating {char_id} (attempt {attempt})...")
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=180) as response:
                data = response.read()
                if len(data) < 1000:
                    print(f"  ⚠ Too small ({len(data)} bytes), retrying...")
                    time.sleep(5)
                    continue
                with open(filepath, 'wb') as f:
                    f.write(data)
                print(f"  ✓ Saved {filename} ({len(data):,} bytes)")
                return True
        except Exception as e:
            print(f"  ✗ Error: {e}")
            if attempt < retries:
                wait = 10 * attempt
                print(f"  Waiting {wait}s before retry...")
                time.sleep(wait)
    return False


def main():
    print(f"Generating {len(CHARACTERS)} character portraits...")
    print(f"Output: {os.path.abspath(PORTRAITS_DIR)}\n")

    success = 0
    for i, (char_id, prompt) in enumerate(CHARACTERS):
        print(f"[{i+1}/{len(CHARACTERS)}] {char_id}")
        if download_portrait(char_id, prompt):
            success += 1
        if i < len(CHARACTERS) - 1:
            time.sleep(3)

    print(f"\n{'='*40}")
    print(f"Generated {success}/{len(CHARACTERS)} portraits")

    print("\nFiles:")
    for f in sorted(os.listdir(PORTRAITS_DIR)):
        size = os.path.getsize(os.path.join(PORTRAITS_DIR, f))
        print(f"  {f}: {size:,} bytes")


if __name__ == '__main__':
    main()
