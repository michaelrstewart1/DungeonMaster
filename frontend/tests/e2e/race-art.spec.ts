/**
 * Generate D&D race portrait art — dark fantasy style, 200x260 card art.
 * Each race gets a distinctive silhouette portrait with atmospheric effects.
 */
import { test } from '@playwright/test';

interface RaceArt {
  id: string;
  name: string;
  palette: { bg1: string; bg2: string; accent: string; glow: string; skin: string };
  scene: string;
}

const RACES: RaceArt[] = [
  {
    id: 'human',
    name: 'Human',
    palette: { bg1: '#1a1520', bg2: '#2a2030', accent: '#c9a84c', glow: '#dabb6e', skin: '#c4956a' },
    scene: `
      <!-- Castle/city backdrop -->
      <rect x="30" y="100" width="20" height="60" fill="#2a2030" stroke="#c9a84c" stroke-width="0.3" opacity="0.4"/>
      <rect x="150" y="90" width="18" height="70" fill="#2a2030" stroke="#c9a84c" stroke-width="0.3" opacity="0.4"/>
      <polygon points="30,100 40,85 50,100" fill="#2a2030" stroke="#c9a84c" stroke-width="0.3" opacity="0.4"/>
      <polygon points="150,90 159,75 168,90" fill="#2a2030" stroke="#c9a84c" stroke-width="0.3" opacity="0.4"/>

      <!-- Human figure — balanced, armored warrior -->
      <g transform="translate(100,80)">
        <!-- Shoulders/armor -->
        <path d="M-22,30 Q-25,20 -18,15 L-8,10 Q0,8 8,10 L18,15 Q25,20 22,30" fill="#4a3a2a" stroke="#c9a84c" stroke-width="0.5"/>
        <!-- Torso -->
        <rect x="-14" y="30" width="28" height="45" rx="3" fill="#3a2a1a" stroke="#8a7a5a" stroke-width="0.5"/>
        <!-- Belt -->
        <rect x="-16" y="65" width="32" height="5" fill="#4a3a2a" stroke="#c9a84c" stroke-width="0.5"/>
        <circle cx="0" cy="67" r="3" fill="#c9a84c" opacity="0.7"/>
        <!-- Neck -->
        <rect x="-5" y="5" width="10" height="8" fill="#c4956a" opacity="0.8"/>
        <!-- Head -->
        <ellipse cx="0" cy="-5" rx="14" ry="16" fill="#c4956a"/>
        <!-- Hair -->
        <path d="M-14,-5 Q-15,-18 -8,-22 Q0,-26 8,-22 Q15,-18 14,-5" fill="#3a2510"/>
        <!-- Eyes -->
        <ellipse cx="-5" cy="-5" rx="2.5" ry="1.5" fill="#1a1510"/>
        <ellipse cx="5" cy="-5" rx="2.5" ry="1.5" fill="#1a1510"/>
        <circle cx="-4.5" cy="-5" r="0.8" fill="#5a7aaa"/>
        <circle cx="5.5" cy="-5" r="0.8" fill="#5a7aaa"/>
        <!-- Nose/mouth -->
        <line x1="0" y1="-3" x2="0" y2="1" stroke="#9a7a5a" stroke-width="0.5"/>
        <path d="M-3,4 Q0,6 3,4" stroke="#8a6a4a" stroke-width="0.5" fill="none"/>
        <!-- Sword hilt at side -->
        <rect x="20" y="35" width="3" height="20" fill="#8a7a5a"/>
        <rect x="17" y="33" width="9" height="3" fill="#c9a84c"/>
      </g>

      <!-- Banner -->
      <rect x="70" y="175" width="60" height="4" fill="#c9a84c" opacity="0.2" rx="2"/>
    `,
  },
  {
    id: 'elf',
    name: 'Elf',
    palette: { bg1: '#0a1a10', bg2: '#1a2a1a', accent: '#70c080', glow: '#90e0a0', skin: '#e0d0b8' },
    scene: `
      <!-- Forest canopy -->
      ${[30,70,110,140].map((x, i) => `
        <path d="M${x},${60+i*10} Q${x+10},${30+i*5} ${x+20},${60+i*10}" fill="#1a3a1a" opacity="${0.3+i*0.1}"/>
      `).join('')}

      <!-- Elven figure — tall, graceful -->
      <g transform="translate(100,70)">
        <!-- Flowing cloak -->
        <path d="M-20,25 Q-30,80 -25,110 L-10,105 L-12,30" fill="#1a3a2a" opacity="0.6"/>
        <path d="M20,25 Q30,80 25,110 L10,105 L12,30" fill="#1a3a2a" opacity="0.6"/>
        <!-- Shoulders -->
        <path d="M-20,25 Q-22,18 -14,14 L-6,11 Q0,10 6,11 L14,14 Q22,18 20,25" fill="#2a4a3a" stroke="#70c080" stroke-width="0.3"/>
        <!-- Torso (lighter armor/robes) -->
        <path d="M-12,25 L-10,70 Q0,74 10,70 L12,25" fill="#1a3520" stroke="#4a8a5a" stroke-width="0.3"/>
        <!-- Decorative line -->
        <line x1="0" y1="28" x2="0" y2="68" stroke="#70c080" stroke-width="0.5" opacity="0.5"/>
        <!-- Neck — longer, more elegant -->
        <rect x="-4" y="4" width="8" height="10" fill="#e0d0b8" opacity="0.8"/>
        <!-- Head — slightly more angular -->
        <ellipse cx="0" cy="-7" rx="12" ry="15" fill="#e0d0b8"/>
        <!-- Pointed ears! -->
        <path d="M-12,-7 L-22,-18 L-14,-10" fill="#e0d0b8"/>
        <path d="M12,-7 L22,-18 L14,-10" fill="#e0d0b8"/>
        <!-- Long hair -->
        <path d="M-12,-7 Q-13,-20 -6,-24 Q0,-27 6,-24 Q13,-20 12,-7" fill="#c8b888"/>
        <path d="M-12,-2 Q-16,20 -14,50" stroke="#c8b888" stroke-width="3" fill="none" opacity="0.4"/>
        <path d="M12,-2 Q16,20 14,50" stroke="#c8b888" stroke-width="3" fill="none" opacity="0.4"/>
        <!-- Eyes — almond-shaped -->
        <path d="M-8,-7 Q-5,-10 -2,-7 Q-5,-5 -8,-7" fill="#70c080"/>
        <path d="M2,-7 Q5,-10 8,-7 Q5,-5 2,-7" fill="#70c080"/>
        <circle cx="-5" cy="-7" r="0.7" fill="#1a3a1a"/>
        <circle cx="5" cy="-7" r="0.7" fill="#1a3a1a"/>
        <!-- Bow over shoulder -->
        <path d="M-18,10 Q-30,-20 -20,-45" stroke="#8a6a3a" stroke-width="1.5" fill="none"/>
        <line x1="-18,10" y1="-20,-45" stroke="#b0a080" stroke-width="0.3"/>
      </g>

      <!-- Leaf particles -->
      ${Array.from({length: 8}, (_, i) => `<path d="M${30+i*18},${170+Math.sin(i)*10} l4,-3 l2,4z" fill="#70c080" opacity="${0.2+i*0.05}"/>`).join('')}
    `,
  },
  {
    id: 'dwarf',
    name: 'Dwarf',
    palette: { bg1: '#1a1008', bg2: '#2a1a0a', accent: '#e08030', glow: '#ff9940', skin: '#c8a080' },
    scene: `
      <!-- Stone/forge backdrop -->
      <rect x="20" y="80" width="160" height="100" fill="#2a1a0a" opacity="0.5"/>
      <!-- Forge glow -->
      <circle cx="100" cy="170" r="40" fill="#e08030" opacity="0.1"/>
      <circle cx="100" cy="170" r="20" fill="#ff9940" opacity="0.1"/>

      <!-- Dwarven figure — short, stocky, bearded -->
      <g transform="translate(100,90)">
        <!-- Broad shoulders with armor plates -->
        <path d="M-28,20 Q-30,10 -20,5 L-8,2 Q0,0 8,2 L20,5 Q30,10 28,20" fill="#5a3a1a" stroke="#e08030" stroke-width="0.5"/>
        <!-- Shoulder studs -->
        <circle cx="-22" cy="12" r="3" fill="#e08030" opacity="0.6"/>
        <circle cx="22" cy="12" r="3" fill="#e08030" opacity="0.6"/>
        <!-- Barrel chest -->
        <rect x="-18" y="20" width="36" height="40" rx="5" fill="#4a2a10" stroke="#8a6a3a" stroke-width="0.5"/>
        <!-- Belt with buckle -->
        <rect x="-20" y="52" width="40" height="6" fill="#5a3a1a" stroke="#e08030" stroke-width="0.5"/>
        <rect x="-4" y="52" width="8" height="6" fill="#e08030" opacity="0.7"/>
        <!-- Thick neck -->
        <rect x="-7" y="-5" width="14" height="10" fill="#c8a080" opacity="0.8"/>
        <!-- Head — wider, more square -->
        <ellipse cx="0" cy="-16" rx="16" ry="14" fill="#c8a080"/>
        <!-- Hair/helmet -->
        <path d="M-16,-16 Q-17,-28 -8,-32 Q0,-35 8,-32 Q17,-28 16,-16" fill="#5a3000"/>
        <!-- Bushy brows -->
        <path d="M-10,-20 Q-5,-23 -1,-20" stroke="#5a3000" stroke-width="2" fill="none"/>
        <path d="M1,-20 Q5,-23 10,-20" stroke="#5a3000" stroke-width="2" fill="none"/>
        <!-- Eyes — deep-set, fierce -->
        <ellipse cx="-5" cy="-17" rx="2" ry="1.5" fill="#1a1000"/>
        <circle cx="-5" cy="-17" r="0.7" fill="#e08030"/>
        <ellipse cx="5" cy="-17" rx="2" ry="1.5" fill="#1a1000"/>
        <circle cx="5" cy="-17" r="0.7" fill="#e08030"/>
        <!-- EPIC BEARD -->
        <path d="M-12,-10 Q-14,5 -12,20 Q-8,30 0,32 Q8,30 12,20 Q14,5 12,-10" fill="#5a3000" opacity="0.9"/>
        <path d="M-8,-8 Q-10,5 -8,18 Q-4,25 0,26" stroke="#7a5010" stroke-width="0.5" fill="none"/>
        <path d="M8,-8 Q10,5 8,18 Q4,25 0,26" stroke="#7a5010" stroke-width="0.5" fill="none"/>
        <!-- Nose -->
        <ellipse cx="0" cy="-12" rx="3" ry="2" fill="#b8906a"/>
        <!-- Axe -->
        <rect x="26" y="0" width="3" height="45" fill="#8a6a3a"/>
        <path d="M24,-5 Q32,-12 38,-2 L29,5" fill="#8a8a9a" stroke="#aaa" stroke-width="0.5"/>
      </g>
    `,
  },
  {
    id: 'halfling',
    name: 'Halfling',
    palette: { bg1: '#1a1a08', bg2: '#2a2810', accent: '#a0c040', glow: '#c0e060', skin: '#d0b890' },
    scene: `
      <!-- Rolling hills backdrop -->
      <ellipse cx="60" cy="180" rx="80" ry="30" fill="#2a3010" opacity="0.5"/>
      <ellipse cx="150" cy="185" rx="70" ry="25" fill="#2a2810" opacity="0.5"/>

      <!-- Halfling figure — small, cheerful -->
      <g transform="translate(100,100)">
        <!-- Simple vest/shirt -->
        <path d="M-16,18 Q-18,12 -12,9 L-5,7 Q0,6 5,7 L12,9 Q18,12 16,18" fill="#5a6a30" stroke="#a0c040" stroke-width="0.3"/>
        <rect x="-10" y="18" width="20" height="35" rx="4" fill="#4a5a20" stroke="#7a8a3a" stroke-width="0.3"/>
        <!-- Vest overlay -->
        <path d="M-8,18 L-6,48 Q0,50 6,48 L8,18" fill="#5a6a30" opacity="0.5"/>
        <!-- Belt -->
        <rect x="-12" y="46" width="24" height="4" fill="#6a5a30" stroke="#a0c040" stroke-width="0.3"/>
        <!-- Neck -->
        <rect x="-4" y="2" width="8" height="8" fill="#d0b890" opacity="0.8"/>
        <!-- Head — round, friendly face -->
        <circle cx="0" cy="-8" r="14" fill="#d0b890"/>
        <!-- Curly hair -->
        <path d="M-14,-8 Q-15,-20 -8,-24 Q0,-27 8,-24 Q15,-20 14,-8" fill="#6a4020"/>
        ${[-10,-5,0,5,10].map(x => `<circle cx="${x}" cy="-22" r="3" fill="#6a4020"/>`).join('')}
        <!-- Bright eyes -->
        <circle cx="-5" cy="-8" r="2.5" fill="white" opacity="0.9"/>
        <circle cx="5" cy="-8" r="2.5" fill="white" opacity="0.9"/>
        <circle cx="-4.5" cy="-8" r="1.2" fill="#4a6a20"/>
        <circle cx="5.5" cy="-8" r="1.2" fill="#4a6a20"/>
        <!-- Happy mouth -->
        <path d="M-5,-1 Q0,3 5,-1" stroke="#8a6a4a" stroke-width="0.8" fill="none"/>
        <!-- Rosy cheeks -->
        <circle cx="-8" cy="-3" r="3" fill="#d0a080" opacity="0.4"/>
        <circle cx="8" cy="-3" r="3" fill="#d0a080" opacity="0.4"/>
        <!-- Pointed sideburns/curly ears -->
        <ellipse cx="-14" cy="-6" rx="3" ry="4" fill="#d0b890"/>
        <ellipse cx="14" cy="-6" rx="3" ry="4" fill="#d0b890"/>
        <!-- Sling/pouch -->
        <circle cx="15" cy="35" r="6" fill="#6a5a30" stroke="#a0c040" stroke-width="0.3"/>
      </g>

      <!-- Flowers/grass -->
      ${Array.from({length: 6}, (_, i) => `<line x1="${30+i*25}" y1="195" x2="${32+i*25}" y2="${185+Math.sin(i)*3}" stroke="#5a7a30" stroke-width="1" opacity="0.4"/>`).join('')}
    `,
  },
  {
    id: 'gnome',
    name: 'Gnome',
    palette: { bg1: '#0a0a1a', bg2: '#1a1530', accent: '#60a0e0', glow: '#80c0ff', skin: '#d8c8a8' },
    scene: `
      <!-- Clockwork/arcane backdrop -->
      <circle cx="50" cy="100" r="30" fill="none" stroke="#60a0e0" stroke-width="0.3" opacity="0.2"/>
      <circle cx="150" cy="90" r="25" fill="none" stroke="#60a0e0" stroke-width="0.3" opacity="0.2"/>
      ${[50,150].map(cx => `<circle cx="${cx}" cy="${cx===50?100:90}" r="${cx===50?18:15}" fill="none" stroke="#60a0e0" stroke-width="0.3" opacity="0.15"/>`).join('')}

      <!-- Gnome figure — tiny, big head, inventive -->
      <g transform="translate(100,95)">
        <!-- Lab coat / robes -->
        <path d="M-14,16 Q-16,10 -10,7 L-4,5 Q0,4 4,5 L10,7 Q16,10 14,16" fill="#2a3050" stroke="#60a0e0" stroke-width="0.3"/>
        <path d="M-10,16 L-12,55 Q0,58 12,55 L10,16" fill="#1a2540" stroke="#4a6a8a" stroke-width="0.3"/>
        <!-- Pockets with stuff sticking out -->
        <rect x="-12" y="38" width="8" height="6" fill="#2a3050" stroke="#60a0e0" stroke-width="0.3"/>
        <rect x="4" y="36" width="8" height="6" fill="#2a3050" stroke="#60a0e0" stroke-width="0.3"/>
        <!-- Neck -->
        <rect x="-3" y="0" width="6" height="6" fill="#d8c8a8" opacity="0.8"/>
        <!-- Head — oversized and round -->
        <circle cx="0" cy="-12" r="16" fill="#d8c8a8"/>
        <!-- Wild hair/hat -->
        <path d="M-16,-12 Q-18,-28 -8,-34 Q0,-38 8,-34 Q18,-28 16,-12" fill="#5040a0"/>
        <polygon points="-2,-34 0,-48 2,-34" fill="#5040a0"/>
        <circle cx="0" cy="-48" r="3" fill="#60a0e0" opacity="0.6"/>
        <!-- Big bright eyes -->
        <circle cx="-6" cy="-12" r="4" fill="white" opacity="0.95"/>
        <circle cx="6" cy="-12" r="4" fill="white" opacity="0.95"/>
        <circle cx="-5.5" cy="-12" r="2" fill="#60a0e0"/>
        <circle cx="6.5" cy="-12" r="2" fill="#60a0e0"/>
        <circle cx="-5" cy="-12.5" r="0.5" fill="white"/>
        <circle cx="7" cy="-12.5" r="0.5" fill="white"/>
        <!-- Small nose -->
        <circle cx="0" cy="-7" r="2.5" fill="#c8b898"/>
        <!-- Grin -->
        <path d="M-5,-2 Q0,2 5,-2" stroke="#8a7a5a" stroke-width="0.8" fill="none"/>
        <!-- Goggles on forehead -->
        <ellipse cx="-6" cy="-22" rx="5" ry="3" fill="none" stroke="#80c0ff" stroke-width="1"/>
        <ellipse cx="6" cy="-22" rx="5" ry="3" fill="none" stroke="#80c0ff" stroke-width="1"/>
        <line x1="-1" y1="-22" x2="1" y2="-22" stroke="#80c0ff" stroke-width="1"/>
        <!-- Wrench -->
        <rect x="14" y="20" width="2" height="25" fill="#8a8a9a" transform="rotate(10,15,30)"/>
      </g>

      <!-- Spark particles -->
      ${Array.from({length: 6}, (_, i) => `<circle cx="${60+i*15}" cy="${160+Math.sin(i*2)*8}" r="1" fill="#80c0ff" opacity="${0.3+i*0.08}"/>`).join('')}
    `,
  },
  {
    id: 'half-elf',
    name: 'Half-Elf',
    palette: { bg1: '#10101a', bg2: '#201a2a', accent: '#b080d0', glow: '#c0a0e0', skin: '#d8c0a8' },
    scene: `
      <!-- Dual nature backdrop — city meets forest -->
      <line x1="100" y1="60" x2="100" y2="200" stroke="#b080d0" stroke-width="0.3" opacity="0.3" stroke-dasharray="2,4"/>
      <rect x="30" y="100" width="15" height="50" fill="#201a2a" opacity="0.4"/>
      <path d="M140,80 Q150,60 160,80" fill="#1a2a1a" opacity="0.3"/>

      <!-- Half-Elf figure — elegant but approachable -->
      <g transform="translate(100,78)">
        <!-- Cloak/outfit blend -->
        <path d="M-20,25 Q-22,18 -15,13 L-7,10 Q0,9 7,10 L15,13 Q22,18 20,25" fill="#3a2a4a" stroke="#b080d0" stroke-width="0.3"/>
        <path d="M-13,25 L-11,68 Q0,72 11,68 L13,25" fill="#2a1a3a" stroke="#6a5a7a" stroke-width="0.3"/>
        <!-- Sash -->
        <path d="M-10,40 Q0,42 10,40" stroke="#b080d0" stroke-width="1.5" fill="none"/>
        <!-- Neck -->
        <rect x="-4" y="4" width="8" height="8" fill="#d8c0a8" opacity="0.8"/>
        <!-- Head -->
        <ellipse cx="0" cy="-7" rx="13" ry="15" fill="#d8c0a8"/>
        <!-- Semi-pointed ears -->
        <path d="M-13,-7 L-19,-14 L-14,-9" fill="#d8c0a8"/>
        <path d="M13,-7 L19,-14 L14,-9" fill="#d8c0a8"/>
        <!-- Flowing hair -->
        <path d="M-13,-7 Q-14,-20 -7,-24 Q0,-27 7,-24 Q14,-20 13,-7" fill="#4a2a1a"/>
        <path d="M-13,-2 Q-15,15 -12,35" stroke="#4a2a1a" stroke-width="2.5" fill="none" opacity="0.5"/>
        <path d="M13,-2 Q15,15 12,35" stroke="#4a2a1a" stroke-width="2.5" fill="none" opacity="0.5"/>
        <!-- Eyes — luminous -->
        <path d="M-8,-7 Q-5,-10 -2,-7 Q-5,-5 -8,-7" fill="#b080d0"/>
        <path d="M2,-7 Q5,-10 8,-7 Q5,-5 2,-7" fill="#b080d0"/>
        <!-- Features -->
        <line x1="0" y1="-4" x2="0" y2="0" stroke="#b8a090" stroke-width="0.4"/>
        <path d="M-3,3 Q0,5 3,3" stroke="#9a8070" stroke-width="0.5" fill="none"/>
        <!-- Lute on back -->
        <ellipse cx="-18" cy="15" rx="7" ry="10" fill="#6a4a2a" stroke="#b080d0" stroke-width="0.3" opacity="0.6"/>
      </g>
    `,
  },
  {
    id: 'half-orc',
    name: 'Half-Orc',
    palette: { bg1: '#0a1008', bg2: '#1a2010', accent: '#80b040', glow: '#a0d060', skin: '#7a9a60' },
    scene: `
      <!-- Harsh terrain backdrop -->
      <polygon points="20,160 60,120 100,165" fill="#1a2010" opacity="0.3"/>
      <polygon points="100,160 150,110 180,165" fill="#1a2010" opacity="0.25"/>

      <!-- Half-Orc figure — massive, intimidating but noble -->
      <g transform="translate(100,72)">
        <!-- Huge shoulders -->
        <path d="M-30,25 Q-34,12 -22,6 L-10,2 Q0,0 10,2 L22,6 Q34,12 30,25" fill="#3a4a20" stroke="#80b040" stroke-width="0.5"/>
        <!-- Fur/hide armor -->
        <rect x="-20" y="25" width="40" height="50" rx="4" fill="#2a3a10" stroke="#5a6a3a" stroke-width="0.5"/>
        <!-- Leather straps crossing -->
        <line x1="-18" y1="28" x2="18" y2="65" stroke="#5a4a20" stroke-width="2"/>
        <line x1="18" y1="28" x2="-18" y2="65" stroke="#5a4a20" stroke-width="2"/>
        <!-- Thick neck -->
        <rect x="-8" y="-2" width="16" height="10" fill="#7a9a60" opacity="0.8"/>
        <!-- Head — broad jaw, strong brow -->
        <path d="M-16,-8 Q-18,-22 -10,-28 Q0,-32 10,-28 Q18,-22 16,-8 Q14,2 10,6 L-10,6 Q-14,2 -16,-8" fill="#7a9a60"/>
        <!-- Heavy brow ridge -->
        <path d="M-14,-18 Q0,-22 14,-18" stroke="#6a8a50" stroke-width="2.5" fill="none"/>
        <!-- Short dark hair -->
        <path d="M-16,-12 Q-17,-24 -10,-30 Q0,-34 10,-30 Q17,-24 16,-12" fill="#2a3010"/>
        <!-- Eyes — intense -->
        <ellipse cx="-6" cy="-14" rx="3" ry="2" fill="#1a2010"/>
        <circle cx="-5.5" cy="-14" r="1" fill="#c0a020"/>
        <ellipse cx="6" cy="-14" rx="3" ry="2" fill="#1a2010"/>
        <circle cx="6.5" cy="-14" r="1" fill="#c0a020"/>
        <!-- Lower fangs/tusks -->
        <polygon points="-6,0 -5,-4 -4,0" fill="#e0e0d0"/>
        <polygon points="4,0 5,-4 6,0" fill="#e0e0d0"/>
        <!-- Nose — broad -->
        <ellipse cx="0" cy="-8" rx="4" ry="2.5" fill="#6a8a50"/>
        <!-- Scar across face -->
        <line x1="-12" y1="-10" x2="2" y2="-4" stroke="#5a7a40" stroke-width="0.8" opacity="0.6"/>
        <!-- Greataxe -->
        <rect x="28" y="-10" width="4" height="60" fill="#5a4a30"/>
        <path d="M25,-15 Q35,-25 42,-10 L32,-2" fill="#7a7a8a" stroke="#9a9aaa" stroke-width="0.5"/>
      </g>
    `,
  },
  {
    id: 'tiefling',
    name: 'Tiefling',
    palette: { bg1: '#1a0810', bg2: '#2a1020', accent: '#d04060', glow: '#e06080', skin: '#b04060' },
    scene: `
      <!-- Infernal backdrop -->
      <circle cx="100" cy="200" r="60" fill="#d04060" opacity="0.05"/>
      ${Array.from({length: 5}, (_, i) => `<path d="M${20+i*35},200 Q${25+i*35},${170-i*5} ${30+i*35},200" stroke="#d04060" stroke-width="0.5" fill="none" opacity="0.15"/>`).join('')}

      <!-- Tiefling figure — demonic elegance -->
      <g transform="translate(100,75)">
        <!-- Shoulders/elegant clothing -->
        <path d="M-20,25 Q-22,16 -14,12 L-6,9 Q0,8 6,9 L14,12 Q22,16 20,25" fill="#3a1020" stroke="#d04060" stroke-width="0.3"/>
        <!-- Ornate robes -->
        <path d="M-12,25 L-14,70 Q0,75 14,70 L12,25" fill="#2a0818" stroke="#8a3050" stroke-width="0.3"/>
        <!-- Infernal sigils -->
        <circle cx="0" cy="42" r="5" fill="none" stroke="#d04060" stroke-width="0.5" opacity="0.4"/>
        <!-- Neck -->
        <rect x="-4" y="4" width="8" height="8" fill="#b04060" opacity="0.8"/>
        <!-- Head -->
        <ellipse cx="0" cy="-7" rx="13" ry="15" fill="#b04060"/>
        <!-- HORNS -->
        <path d="M-10,-18 Q-14,-30 -18,-38 Q-16,-36 -12,-28" fill="#4a1020" stroke="#6a2030" stroke-width="0.5"/>
        <path d="M10,-18 Q14,-30 18,-38 Q16,-36 12,-28" fill="#4a1020" stroke="#6a2030" stroke-width="0.5"/>
        <!-- Dark hair -->
        <path d="M-13,-7 Q-14,-18 -8,-22 Q0,-25 8,-22 Q14,-18 13,-7" fill="#1a0510"/>
        <path d="M-13,-2 Q-16,20 -14,45" stroke="#1a0510" stroke-width="2" fill="none" opacity="0.4"/>
        <!-- Glowing eyes -->
        <ellipse cx="-5" cy="-7" rx="2.5" ry="2" fill="#ffcc00" opacity="0.9"/>
        <ellipse cx="5" cy="-7" rx="2.5" ry="2" fill="#ffcc00" opacity="0.9"/>
        <circle cx="-5" cy="-7" r="0.8" fill="#ff4400"/>
        <circle cx="5" cy="-7" r="0.8" fill="#ff4400"/>
        <!-- Sharp features -->
        <line x1="0" y1="-3" x2="0" y2="0" stroke="#903050" stroke-width="0.4"/>
        <path d="M-3,3 Q0,4 3,3" stroke="#803040" stroke-width="0.5" fill="none"/>
        <!-- Tail -->
        <path d="M5,65 Q20,55 25,40 Q28,30 22,25" stroke="#b04060" stroke-width="2" fill="none"/>
        <polygon points="22,25 18,22 20,28" fill="#b04060"/>
      </g>

      <!-- Subtle flame particles -->
      ${Array.from({length: 5}, (_, i) => `<circle cx="${70+i*15}" cy="${175-i*3}" r="${1+i%2}" fill="#d04060" opacity="${0.15+i*0.05}"/>`).join('')}
    `,
  },
  {
    id: 'dragonborn',
    name: 'Dragonborn',
    palette: { bg1: '#0a0a18', bg2: '#1a1a2a', accent: '#4090d0', glow: '#60b0f0', skin: '#3a6a9a' },
    scene: `
      <!-- Draconic atmosphere -->
      <circle cx="100" cy="60" r="30" fill="#4090d0" opacity="0.06"/>

      <!-- Dragonborn figure — powerful, reptilian -->
      <g transform="translate(100,68)">
        <!-- Massive armored shoulders -->
        <path d="M-30,28 Q-35,14 -24,6 L-10,2 Q0,0 10,2 L24,6 Q35,14 30,28" fill="#2a4060" stroke="#4090d0" stroke-width="0.5"/>
        <!-- Shoulder spines -->
        <polygon points="-28,15 -32,5 -26,12" fill="#3a6a9a"/>
        <polygon points="28,15 32,5 26,12" fill="#3a6a9a"/>
        <!-- Heavy plate armor torso -->
        <rect x="-18" y="28" width="36" height="48" rx="3" fill="#1a3050" stroke="#4a7090" stroke-width="0.5"/>
        <!-- Chest plate detail -->
        <path d="M-10,32 L0,45 L10,32" fill="none" stroke="#4090d0" stroke-width="0.5" opacity="0.5"/>
        <!-- Thick scaled neck -->
        <rect x="-8" y="-2" width="16" height="12" fill="#3a6a9a" opacity="0.8"/>
        <!-- Draconic head — snout, ridges -->
        <path d="M-16,-8 Q-18,-22 -12,-30 Q0,-38 12,-30 Q18,-22 16,-8 Q12,2 8,4 L-8,4 Q-12,2 -16,-8" fill="#3a6a9a"/>
        <!-- Snout -->
        <path d="M-8,0 Q0,8 8,0" fill="#2a5a8a"/>
        <!-- Nostril slits -->
        <ellipse cx="-3" cy="2" rx="1" ry="0.5" fill="#1a3a5a"/>
        <ellipse cx="3" cy="2" rx="1" ry="0.5" fill="#1a3a5a"/>
        <!-- Head ridges/crest -->
        <path d="M-10,-28 Q-12,-35 -8,-40" stroke="#3a6a9a" stroke-width="2" fill="none"/>
        <path d="M0,-30 Q0,-38 0,-44" stroke="#3a6a9a" stroke-width="2" fill="none"/>
        <path d="M10,-28 Q12,-35 8,-40" stroke="#3a6a9a" stroke-width="2" fill="none"/>
        <!-- Fierce eyes -->
        <path d="M-9,-16 L-4,-18 L-9,-14 Z" fill="#ffaa20"/>
        <path d="M9,-16 L4,-18 L9,-14 Z" fill="#ffaa20"/>
        <circle cx="-7" cy="-16" r="0.8" fill="#1a1a2a"/>
        <circle cx="7" cy="-16" r="0.8" fill="#1a1a2a"/>
        <!-- Jaw ridge -->
        <path d="M-12,-6 Q0,-2 12,-6" stroke="#2a5a8a" stroke-width="0.8" fill="none"/>
        <!-- Scale pattern on neck -->
        ${[-4,-1,2,5].map(y => `<path d="M-6,${y} Q0,${y-2} 6,${y}" stroke="#4a7a9a" stroke-width="0.3" fill="none" opacity="0.4"/>`).join('')}
        <!-- Breath weapon glow from mouth -->
        <ellipse cx="0" cy="6" rx="4" ry="2" fill="#4090d0" opacity="0.2"/>
        <!-- Shield -->
        <path d="M-28,30 L-35,28 L-38,50 L-32,55 L-26,50 Z" fill="#2a4060" stroke="#4090d0" stroke-width="0.5"/>
      </g>
    `,
  },
];

test.describe('Race Art Generation', () => {
  for (const race of RACES) {
    test(`Generate: ${race.name}`, async ({ browser }) => {
      const ctx = await browser.newContext({ viewport: { width: 200, height: 260 } });
      const page = await ctx.newPage();

      const svg = `
        <svg xmlns="http://www.w3.org/2000/svg" width="200" height="260" viewBox="0 0 200 260">
          <defs>
            <linearGradient id="bg" x1="0" y1="0" x2="0.3" y2="1">
              <stop offset="0%" stop-color="${race.palette.bg1}"/>
              <stop offset="100%" stop-color="${race.palette.bg2}"/>
            </linearGradient>
            <radialGradient id="glow" cx="0.5" cy="0.4" r="0.5">
              <stop offset="0%" stop-color="${race.palette.glow}" stop-opacity="0.12"/>
              <stop offset="100%" stop-color="${race.palette.bg1}" stop-opacity="0"/>
            </radialGradient>
          </defs>
          <rect width="200" height="260" fill="url(#bg)"/>
          <rect width="200" height="260" fill="url(#glow)"/>
          ${race.scene}
          <!-- Name banner -->
          <rect x="0" y="215" width="200" height="45" fill="${race.palette.bg1}" opacity="0.85"/>
          <line x1="10" y1="220" x2="190" y2="220" stroke="${race.palette.accent}" stroke-width="0.5" opacity="0.5"/>
          <text x="100" y="244" text-anchor="middle" font-family="Georgia, 'Times New Roman', serif" font-size="16" font-weight="bold" fill="${race.palette.accent}" letter-spacing="2">${race.name.toUpperCase()}</text>
          <rect x="0" y="0" width="200" height="260" fill="none" stroke="${race.palette.accent}" stroke-width="0.5" opacity="0.3" rx="4"/>
        </svg>
      `;

      await page.setContent(`<html><head><style>*{margin:0;padding:0;}body{width:200px;height:260px;overflow:hidden;}</style></head><body>${svg}</body></html>`);
      await page.screenshot({ path: `../../public/art/races/${race.id}.png`, clip: { x: 0, y: 0, width: 200, height: 260 } });
      await ctx.close();
    });
  }
});
