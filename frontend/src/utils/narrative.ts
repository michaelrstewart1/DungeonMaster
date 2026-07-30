/** Narrative text helpers shared by story-feed views. */

// "86993578-beda-4ca6-b118-428df53d748e: I attack" → "I attack".
// Sessions recorded before character-name resolution stored raw character
// UUIDs as the speaker label; never show those to humans.
const UUID_LABEL =
  /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}:\s*/i;

export function stripUuidLabel(text: string): string {
  return text.replace(UUID_LABEL, '');
}
