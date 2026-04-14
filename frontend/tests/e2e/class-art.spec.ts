/**
 * Generate D&D class portrait art — dark fantasy style, 200x260 card art.
 * Each class gets an iconic silhouette with atmospheric effects.
 */
import { test } from '@playwright/test';

interface ClassArt {
  id: string;
  name: string;
  palette: { bg1: string; bg2: string; accent: string; glow: string };
  scene: string;
}

const CLASSES: ClassArt[] = [
  {
    id: 'barbarian',
    name: 'Barbarian',
    palette: { bg1: '#1a0808', bg2: '#2a1010', accent: '#e04040', glow: '#ff6060' },
    scene: `
      <!-- Rage aura -->
      <circle cx="100" cy="110" r="50" fill="#e04040" opacity="0.06"/>
      <circle cx="100" cy="110" r="30" fill="#ff6060" opacity="0.05"/>

      <!-- Barbarian — massive, primal fury -->
      <g transform="translate(100,70)">
        <!-- Bare muscular torso -->
        <path d="M-28,28 Q-32,14 -22,6 L-10,2 Q0,-1 10,2 L22,6 Q32,14 28,28" fill="#8a5a3a" stroke="#e04040" stroke-width="0.3"/>
        <rect x="-18" y="28" width="36" height="45" rx="3" fill="#7a4a2a"/>
        <!-- Warpaint stripes -->
        <line x1="-12" y1="32" x2="-12" y2="55" stroke="#e04040" stroke-width="1.5" opacity="0.6"/>
        <line x1="12" y1="32" x2="12" y2="55" stroke="#e04040" stroke-width="1.5" opacity="0.6"/>
        <!-- Fur loincloth -->
        <path d="M-20,65 Q0,80 20,65" fill="#4a2a10" stroke="#6a4020" stroke-width="0.5"/>
        <!-- Thick neck -->
        <rect x="-8" y="-4" width="16" height="10" fill="#8a5a3a"/>
        <!-- Head -->
        <ellipse cx="0" cy="-15" rx="14" ry="14" fill="#8a5a3a"/>
        <!-- Wild mane -->
        <path d="M-14,-15 Q-16,-30 -10,-35 Q0,-40 10,-35 Q16,-30 14,-15" fill="#3a1a08"/>
        <path d="M-14,-10 Q-20,-5 -22,5" stroke="#3a1a08" stroke-width="3" fill="none"/>
        <path d="M14,-10 Q20,-5 22,5" stroke="#3a1a08" stroke-width="3" fill="none"/>
        <!-- Fierce eyes -->
        <ellipse cx="-5" cy="-15" rx="2.5" ry="2" fill="#ff2020" opacity="0.8"/>
        <ellipse cx="5" cy="-15" rx="2.5" ry="2" fill="#ff2020" opacity="0.8"/>
        <!-- Warpaint on face -->
        <line x1="-10" y1="-12" x2="-2" y2="-12" stroke="#e04040" stroke-width="1.5"/>
        <line x1="2" y1="-12" x2="10" y2="-12" stroke="#e04040" stroke-width="1.5"/>
        <!-- Snarl -->
        <path d="M-5,-5 Q0,-3 5,-5" stroke="#6a3a1a" stroke-width="1" fill="none"/>
        <!-- GREATAXE -->
        <rect x="26" y="-20" width="4" height="70" fill="#5a3a1a"/>
        <path d="M22,-25 Q34,-40 42,-20 L30,-12" fill="#8a8a9a" stroke="#aaa" stroke-width="0.5"/>
        <path d="M22,-15 Q34,0 42,-20" fill="none" stroke="#aaa" stroke-width="0.3"/>
      </g>
    `,
  },
  {
    id: 'bard',
    name: 'Bard',
    palette: { bg1: '#10081a', bg2: '#201530', accent: '#c070e0', glow: '#d090f0' },
    scene: `
      <!-- Musical notes floating -->
      ${['♪','♫','♬'].map((_, i) => `<circle cx="${50+i*40}" cy="${70+i*15}" r="3" fill="#c070e0" opacity="${0.15+i*0.05}"/>`).join('')}

      <!-- Bard — charismatic performer -->
      <g transform="translate(100,78)">
        <path d="M-18,22 Q-20,15 -13,11 L-5,8 Q0,7 5,8 L13,11 Q20,15 18,22" fill="#3a2050" stroke="#c070e0" stroke-width="0.3"/>
        <path d="M-11,22 L-13,65 Q0,70 13,65 L11,22" fill="#2a1540" stroke="#6a4a7a" stroke-width="0.3"/>
        <!-- Flamboyant cape -->
        <path d="M-18,22 Q-28,50 -22,75" stroke="#c070e0" stroke-width="1" fill="none" opacity="0.4"/>
        <path d="M18,22 Q28,50 22,75" stroke="#c070e0" stroke-width="1" fill="none" opacity="0.4"/>
        <rect x="-4" y="3" width="8" height="8" fill="#d0b098" opacity="0.8"/>
        <ellipse cx="0" cy="-8" rx="12" ry="14" fill="#d0b098"/>
        <path d="M-12,-8 Q-13,-20 -6,-24 Q0,-27 6,-24 Q13,-20 12,-8" fill="#4a2a3a"/>
        <!-- Feathered hat -->
        <path d="M-12,-18 Q-8,-28 5,-26 Q15,-24 14,-16" fill="#3a1540" stroke="#c070e0" stroke-width="0.3"/>
        <path d="M10,-24 Q18,-35 22,-28" stroke="#c070e0" stroke-width="1" fill="none"/>
        <!-- Charming eyes -->
        <ellipse cx="-5" cy="-8" rx="2" ry="1.5" fill="#c070e0"/>
        <ellipse cx="5" cy="-8" rx="2" ry="1.5" fill="#c070e0"/>
        <!-- Smirk -->
        <path d="M-3,-1 Q2,2 5,0" stroke="#a08070" stroke-width="0.6" fill="none"/>
        <!-- LUTE -->
        <g transform="translate(-20,20) rotate(-15)">
          <ellipse cx="0" cy="10" rx="10" ry="14" fill="#6a4020" stroke="#c070e0" stroke-width="0.3"/>
          <ellipse cx="0" cy="10" rx="3" ry="3" fill="#3a2010"/>
          <rect x="-1.5" y="-20" width="3" height="25" fill="#8a6030"/>
          ${[-3,-1,1,3].map(x => `<line x1="${x}" y1="-18" x2="${x}" y2="20" stroke="#e0c080" stroke-width="0.2" opacity="0.5"/>`).join('')}
        </g>
      </g>

      <!-- Sound wave arcs -->
      ${[20,30,40].map((r, i) => `<path d="M${60-r},${130} A${r},${r} 0 0 1 ${60+r},${130}" fill="none" stroke="#c070e0" stroke-width="0.4" opacity="${0.15-i*0.04}"/>`).join('')}
    `,
  },
  {
    id: 'cleric',
    name: 'Cleric',
    palette: { bg1: '#101018', bg2: '#1a1a2a', accent: '#e0c040', glow: '#ffe060' },
    scene: `
      <!-- Divine light from above -->
      <path d="M80,0 L90,100 L110,100 L120,0" fill="#e0c040" opacity="0.04"/>

      <g transform="translate(100,78)">
        <path d="M-18,22 Q-20,15 -13,11 L-5,8 Q0,7 5,8 L13,11 Q20,15 18,22" fill="#2a2a3a" stroke="#e0c040" stroke-width="0.4"/>
        <path d="M-12,22 L-14,68 Q0,72 14,68 L12,22" fill="#1a1a2a" stroke="#4a4a5a" stroke-width="0.3"/>
        <!-- Holy symbol on chest -->
        <line x1="0" y1="30" x2="0" y2="50" stroke="#e0c040" stroke-width="1.5" opacity="0.6"/>
        <line x1="-7" y1="38" x2="7" y2="38" stroke="#e0c040" stroke-width="1.5" opacity="0.6"/>
        <rect x="-4" y="3" width="8" height="8" fill="#c8b098" opacity="0.8"/>
        <ellipse cx="0" cy="-8" rx="12" ry="14" fill="#c8b098"/>
        <path d="M-12,-8 Q-13,-20 -6,-24 Q0,-27 6,-24 Q13,-20 12,-8" fill="#2a2030"/>
        <!-- Hood -->
        <path d="M-14,-4 Q-16,-16 -8,-24 Q0,-30 8,-24 Q16,-16 14,-4" fill="#2a2a3a" stroke="#e0c040" stroke-width="0.3" opacity="0.6"/>
        <!-- Serene eyes -->
        <ellipse cx="-5" cy="-8" rx="2" ry="1.5" fill="#e0c040" opacity="0.7"/>
        <ellipse cx="5" cy="-8" rx="2" ry="1.5" fill="#e0c040" opacity="0.7"/>
        <path d="M-3,-1 Q0,1 3,-1" stroke="#9a8a6a" stroke-width="0.5" fill="none"/>
        <!-- MACE + SHIELD -->
        <rect x="20" y="15" width="3" height="35" fill="#8a8a9a"/>
        <circle cx="21" cy="12" r="6" fill="#8a8a9a" stroke="#e0c040" stroke-width="0.5"/>
        <path d="M-24,25 L-30,23 L-33,45 L-27,50 L-21,45 Z" fill="#2a2a4a" stroke="#e0c040" stroke-width="0.5"/>
        <!-- Shield cross -->
        <line x1="-27" y1="30" x2="-27" y2="44" stroke="#e0c040" stroke-width="0.8"/>
        <line x1="-33" y1="37" x2="-21" y2="37" stroke="#e0c040" stroke-width="0.8"/>
      </g>

      <!-- Halo -->
      <ellipse cx="100" cy="60" rx="18" ry="4" fill="none" stroke="#e0c040" stroke-width="0.8" opacity="0.3"/>
    `,
  },
  {
    id: 'druid',
    name: 'Druid',
    palette: { bg1: '#081208', bg2: '#142014', accent: '#40b060', glow: '#60d080' },
    scene: `
      <!-- Living vines backdrop -->
      ${[30,60,140,170].map((x, i) => `<path d="M${x},200 Q${x+5},${150-i*10} ${x-3},${100-i*15}" stroke="#40b060" stroke-width="${1+i*0.3}" fill="none" opacity="${0.15+i*0.03}"/>`).join('')}

      <g transform="translate(100,80)">
        <path d="M-16,20 Q-18,14 -12,10 L-5,7 Q0,6 5,7 L12,10 Q18,14 16,20" fill="#1a3a1a" stroke="#40b060" stroke-width="0.3"/>
        <path d="M-10,20 L-12,65 Q0,70 12,65 L10,20" fill="#102810" stroke="#2a5a2a" stroke-width="0.3"/>
        <!-- Leaf patterns -->
        ${[30,40,50].map(y => `<path d="M-4,${y} Q0,${y-4} 4,${y}" stroke="#40b060" stroke-width="0.5" fill="none" opacity="0.3"/>`).join('')}
        <rect x="-4" y="3" width="8" height="7" fill="#b0a880" opacity="0.8"/>
        <ellipse cx="0" cy="-7" rx="12" ry="13" fill="#b0a880"/>
        <!-- Wild hair with leaves -->
        <path d="M-12,-7 Q-14,-20 -6,-24 Q0,-28 6,-24 Q14,-20 12,-7" fill="#2a4a10"/>
        <path d="M-12,-2 Q-18,10 -16,30" stroke="#2a4a10" stroke-width="3" fill="none" opacity="0.5"/>
        <path d="M12,-2 Q18,10 16,30" stroke="#2a4a10" stroke-width="3" fill="none" opacity="0.5"/>
        <!-- Leaf in hair -->
        <path d="M8,-22 L14,-28 L10,-20" fill="#40b060" opacity="0.6"/>
        <!-- Eyes — nature's wisdom -->
        <ellipse cx="-5" cy="-7" rx="2" ry="1.5" fill="#40b060"/>
        <ellipse cx="5" cy="-7" rx="2" ry="1.5" fill="#40b060"/>
        <path d="M-3,0 Q0,1 3,0" stroke="#8a7a50" stroke-width="0.5" fill="none"/>
        <!-- Wooden staff with crystal -->
        <rect x="18" y="-30" width="3" height="80" fill="#5a3a1a" rx="1"/>
        <path d="M17,-30 Q19.5,-42 22,-30" fill="#2a4a10" stroke="#40b060" stroke-width="0.5"/>
        <circle cx="19.5" cy="-35" r="3" fill="#60d080" opacity="0.5"/>
        <!-- Antler crown -->
        <path d="M-8,-20 Q-12,-30 -15,-35 Q-12,-33 -10,-28" stroke="#6a5a3a" stroke-width="1" fill="none"/>
        <path d="M8,-20 Q12,-30 15,-35 Q12,-33 10,-28" stroke="#6a5a3a" stroke-width="1" fill="none"/>
      </g>
    `,
  },
  {
    id: 'fighter',
    name: 'Fighter',
    palette: { bg1: '#101015', bg2: '#1a1a22', accent: '#8090b0', glow: '#a0b0d0' },
    scene: `
      <g transform="translate(100,72)">
        <!-- Full plate armor -->
        <path d="M-26,26 Q-30,14 -20,6 L-8,2 Q0,0 8,2 L20,6 Q30,14 26,26" fill="#3a3a4a" stroke="#8090b0" stroke-width="0.5"/>
        <!-- Pauldrons -->
        <ellipse cx="-24" cy="16" rx="8" ry="6" fill="#4a4a5a" stroke="#8090b0" stroke-width="0.3"/>
        <ellipse cx="24" cy="16" rx="8" ry="6" fill="#4a4a5a" stroke="#8090b0" stroke-width="0.3"/>
        <!-- Breastplate -->
        <rect x="-16" y="26" width="32" height="45" rx="3" fill="#3a3a44" stroke="#6a6a7a" stroke-width="0.5"/>
        <!-- Plate lines -->
        <line x1="-14" y1="40" x2="14" y2="40" stroke="#5a5a6a" stroke-width="0.5"/>
        <line x1="-14" y1="55" x2="14" y2="55" stroke="#5a5a6a" stroke-width="0.5"/>
        <!-- Belt -->
        <rect x="-18" y="63" width="36" height="5" fill="#4a3a2a" stroke="#8090b0" stroke-width="0.3"/>
        <!-- Helm -->
        <path d="M-14,-4 Q-16,-18 -10,-26 Q0,-32 10,-26 Q16,-18 14,-4 Q10,2 0,4 Q-10,2 -14,-4" fill="#4a4a5a" stroke="#8090b0" stroke-width="0.5"/>
        <!-- Visor slit -->
        <path d="M-8,-10 L8,-10" stroke="#1a1a22" stroke-width="2.5"/>
        <!-- Helm crest -->
        <path d="M0,-28 Q0,-38 -3,-42" stroke="#e04040" stroke-width="2" fill="none"/>
        <path d="M0,-28 Q2,-36 5,-40" stroke="#e04040" stroke-width="1.5" fill="none"/>
        <!-- Nose guard -->
        <line x1="0" y1="-18" x2="0" y2="-6" stroke="#6a6a7a" stroke-width="1.5"/>
        <!-- SWORD -->
        <rect x="22" y="-15" width="3" height="55" fill="#8a8a9a"/>
        <rect x="18" y="-17" width="11" height="3" fill="#8090b0"/>
        <circle cx="23.5" cy="-20" r="2" fill="#8090b0"/>
        <!-- SHIELD -->
        <path d="M-26,28 L-36,26 L-38,55 L-32,60 L-24,55 Z" fill="#3a3a5a" stroke="#8090b0" stroke-width="0.5"/>
        <path d="M-32,35 L-32,52" stroke="#8090b0" stroke-width="0.8"/>
        <path d="M-38,43 L-24,43" stroke="#8090b0" stroke-width="0.8"/>
      </g>
    `,
  },
  {
    id: 'monk',
    name: 'Monk',
    palette: { bg1: '#0a0a10', bg2: '#181820', accent: '#e0a030', glow: '#f0c050' },
    scene: `
      <!-- Ki energy circle -->
      <circle cx="100" cy="110" r="40" fill="none" stroke="#e0a030" stroke-width="0.5" opacity="0.15"/>
      <circle cx="100" cy="110" r="25" fill="none" stroke="#e0a030" stroke-width="0.3" opacity="0.1"/>

      <g transform="translate(100,80)">
        <!-- Simple robes -->
        <path d="M-15,18 Q-17,12 -10,8 L-4,6 Q0,5 4,6 L10,8 Q17,12 15,18" fill="#2a2520" stroke="#e0a030" stroke-width="0.2"/>
        <path d="M-10,18 L-12,65 Q0,68 12,65 L10,18" fill="#1a1810" stroke="#3a3520" stroke-width="0.3"/>
        <!-- Robe sash -->
        <path d="M-8,30 Q0,34 8,30" stroke="#e0a030" stroke-width="1.5" fill="none"/>
        <path d="M6,30 L8,55" stroke="#e0a030" stroke-width="1" fill="none" opacity="0.5"/>
        <rect x="-3" y="2" width="6" height="7" fill="#b89868" opacity="0.8"/>
        <ellipse cx="0" cy="-6" rx="11" ry="13" fill="#b89868"/>
        <!-- Shaved/short hair -->
        <path d="M-11,-6 Q-12,-16 -6,-20 Q0,-23 6,-20 Q12,-16 11,-6" fill="#3a2810" opacity="0.6"/>
        <!-- Serene focused eyes -->
        <path d="M-6,-6 Q-4,-8 -2,-6" stroke="#1a1810" stroke-width="0.8" fill="none"/>
        <path d="M2,-6 Q4,-8 6,-6" stroke="#1a1810" stroke-width="0.8" fill="none"/>
        <!-- Calm expression -->
        <path d="M-2,1 Q0,2 2,1" stroke="#8a7858" stroke-width="0.5" fill="none"/>
        <!-- FISTS in martial pose -->
        <circle cx="-20" cy="25" r="5" fill="#b89868" stroke="#e0a030" stroke-width="0.3"/>
        <circle cx="20" cy="35" r="5" fill="#b89868" stroke="#e0a030" stroke-width="0.3"/>
        <!-- Ki glow from hands -->
        <circle cx="-20" cy="25" r="8" fill="#e0a030" opacity="0.08"/>
        <circle cx="20" cy="35" r="8" fill="#e0a030" opacity="0.08"/>
      </g>

      <!-- Yin-yang symbol -->
      <circle cx="100" cy="185" r="8" fill="none" stroke="#e0a030" stroke-width="0.5" opacity="0.2"/>
    `,
  },
  {
    id: 'paladin',
    name: 'Paladin',
    palette: { bg1: '#0a0a15', bg2: '#151525', accent: '#e0c050', glow: '#f0d870' },
    scene: `
      <!-- Divine light -->
      <path d="M85,0 L95,90 L105,90 L115,0" fill="#e0c050" opacity="0.03"/>

      <g transform="translate(100,70)">
        <!-- Gleaming plate -->
        <path d="M-26,26 Q-30,14 -20,6 L-8,2 Q0,0 8,2 L20,6 Q30,14 26,26" fill="#4a4a5a" stroke="#e0c050" stroke-width="0.5"/>
        <!-- Golden pauldrons -->
        <ellipse cx="-24" cy="16" rx="8" ry="6" fill="#5a5a6a" stroke="#e0c050" stroke-width="0.5"/>
        <ellipse cx="24" cy="16" rx="8" ry="6" fill="#5a5a6a" stroke="#e0c050" stroke-width="0.5"/>
        <rect x="-16" y="26" width="32" height="46" rx="3" fill="#3a3a4a" stroke="#5a5a6a" stroke-width="0.5"/>
        <!-- Holy emblem on chest -->
        <circle cx="0" cy="42" r="8" fill="none" stroke="#e0c050" stroke-width="0.8" opacity="0.5"/>
        <line x1="0" y1="35" x2="0" y2="49" stroke="#e0c050" stroke-width="0.8" opacity="0.5"/>
        <line x1="-7" y1="42" x2="7" y2="42" stroke="#e0c050" stroke-width="0.8" opacity="0.5"/>
        <!-- Cape -->
        <path d="M-24,20 Q-35,50 -28,80" fill="#1a1a40" stroke="#e0c050" stroke-width="0.3" opacity="0.5"/>
        <path d="M24,20 Q35,50 28,80" fill="#1a1a40" stroke="#e0c050" stroke-width="0.3" opacity="0.5"/>
        <!-- Helm with golden accents -->
        <path d="M-14,-4 Q-16,-18 -10,-26 Q0,-32 10,-26 Q16,-18 14,-4 Q10,2 0,4 Q-10,2 -14,-4" fill="#4a4a5a" stroke="#e0c050" stroke-width="0.5"/>
        <line x1="0" y1="-28" x2="0" y2="-6" stroke="#e0c050" stroke-width="1"/>
        <path d="M-8,-10 L8,-10" stroke="#1a1a25" stroke-width="2"/>
        <!-- HOLY SWORD glowing -->
        <rect x="24" y="-20" width="3" height="60" fill="#c0c0d0"/>
        <rect x="20" y="-22" width="11" height="3" fill="#e0c050"/>
        <rect x="24" y="-20" width="3" height="60" fill="#e0c050" opacity="0.15"/>
      </g>

      <!-- Halo glow -->
      <ellipse cx="100" cy="56" rx="20" ry="5" fill="none" stroke="#e0c050" stroke-width="0.8" opacity="0.25"/>
    `,
  },
  {
    id: 'ranger',
    name: 'Ranger',
    palette: { bg1: '#080e08', bg2: '#152015', accent: '#60a060', glow: '#80c080' },
    scene: `
      <!-- Forest silhouette -->
      ${[25,55,135,165].map((x, i) => `<rect x="${x}" y="${70+i*8}" width="4" height="${90-i*10}" fill="#152015" opacity="${0.3+i*0.05}"/><polygon points="${x-4},${70+i*8} ${x+2},${50+i*5} ${x+8},${70+i*8}" fill="#152015" opacity="${0.25+i*0.05}"/>`).join('')}

      <g transform="translate(100,78)">
        <path d="M-18,22 Q-20,15 -13,10 L-5,7 Q0,6 5,7 L13,10 Q20,15 18,22" fill="#2a3520" stroke="#60a060" stroke-width="0.3"/>
        <path d="M-11,22 L-12,65 Q0,68 12,65 L11,22" fill="#1a2a15" stroke="#3a5a3a" stroke-width="0.3"/>
        <!-- Cloak -->
        <path d="M-18,22 Q-26,45 -22,70" fill="#1a2a10" opacity="0.5"/>
        <path d="M18,22 Q26,45 22,70" fill="#1a2a10" opacity="0.5"/>
        <!-- Hood up -->
        <path d="M-15,4 Q-18,-12 -10,-22 Q0,-28 10,-22 Q18,-12 15,4" fill="#2a3520" stroke="#60a060" stroke-width="0.3"/>
        <!-- Face in shadow -->
        <ellipse cx="0" cy="-6" rx="10" ry="12" fill="#b0a080"/>
        <!-- Eyes — sharp, watchful -->
        <path d="M-6,-6 Q-4,-9 -2,-6" fill="#60a060"/>
        <path d="M2,-6 Q4,-9 6,-6" fill="#60a060"/>
        <path d="M-3,1 Q0,2 3,1" stroke="#8a7a5a" stroke-width="0.5" fill="none"/>
        <!-- BOW drawn -->
        <path d="M-22,-10 Q-35,20 -22,50" stroke="#6a4a2a" stroke-width="2" fill="none"/>
        <line x1="-22" y1="-10" x2="-22" y2="50" stroke="#c0b090" stroke-width="0.3"/>
        <!-- Arrow nocked -->
        <line x1="-20" y1="20" x2="8" y2="20" stroke="#5a4a2a" stroke-width="1"/>
        <polygon points="8,18 14,20 8,22" fill="#8a8a9a"/>
        <!-- Quiver on back -->
        <rect x="16" y="-5" width="6" height="35" fill="#4a3a1a" stroke="#60a060" stroke-width="0.3" rx="2"/>
        ${[0,3,6].map(y => `<line x1="17" y1="${-3+y}" x2="22" y2="${-5+y}" stroke="#5a4a2a" stroke-width="0.5"/>`).join('')}
      </g>
    `,
  },
  {
    id: 'rogue',
    name: 'Rogue',
    palette: { bg1: '#0a0810', bg2: '#1a1520', accent: '#8070a0', glow: '#a090c0' },
    scene: `
      <!-- Shadow/smoke -->
      <circle cx="100" cy="130" r="50" fill="#0a0810" opacity="0.3"/>

      <g transform="translate(100,80)">
        <!-- Leather armor, tight-fitting -->
        <path d="M-16,20 Q-18,14 -12,10 L-5,7 Q0,6 5,7 L12,10 Q18,14 16,20" fill="#2a1a2a" stroke="#8070a0" stroke-width="0.3"/>
        <path d="M-10,20 L-11,62 Q0,66 11,62 L10,20" fill="#1a1018" stroke="#3a2a3a" stroke-width="0.3"/>
        <!-- Buckles -->
        ${[30,40,50].map(y => `<rect x="-2" y="${y}" width="4" height="2" fill="#8070a0" opacity="0.4"/>`).join('')}
        <!-- Hood/cowl -->
        <path d="M-14,4 Q-16,-10 -10,-20 Q0,-26 10,-20 Q16,-10 14,4" fill="#1a1018" stroke="#8070a0" stroke-width="0.3"/>
        <ellipse cx="0" cy="-4" rx="10" ry="11" fill="#c0a888"/>
        <!-- Half-shadowed face -->
        <path d="M0,-15 L0,5 Q-10,3 -10,-4 Q-10,-12 0,-15" fill="#1a1018" opacity="0.3"/>
        <!-- One eye visible, one in shadow -->
        <path d="M2,-5 Q4,-7 6,-5" fill="#8070a0"/>
        <circle cx="4" cy="-5.5" r="0.5" fill="#1a1018"/>
        <path d="M-6,-5 Q-4,-7 -2,-5" fill="#8070a0" opacity="0.4"/>
        <!-- Smirk -->
        <path d="M0,1 Q3,2 5,1" stroke="#9a8a6a" stroke-width="0.5" fill="none"/>
        <!-- DUAL DAGGERS -->
        <rect x="-22" y="15" width="2" height="22" fill="#9a9ab0" transform="rotate(-15,-21,26)"/>
        <rect x="-23" y="13" width="4" height="3" fill="#8070a0" transform="rotate(-15,-21,14.5)"/>
        <rect x="20" y="15" width="2" height="22" fill="#9a9ab0" transform="rotate(15,21,26)"/>
        <rect x="19" y="13" width="4" height="3" fill="#8070a0" transform="rotate(15,21,14.5)"/>
      </g>

      <!-- Shadow tendrils -->
      ${[60,80,120,140].map((x, i) => `<path d="M${x},200 Q${x+3},${180-i*5} ${x-2},${165-i*8}" stroke="#1a1018" stroke-width="${2-i*0.3}" fill="none" opacity="${0.2+i*0.03}"/>`).join('')}
    `,
  },
  {
    id: 'sorcerer',
    name: 'Sorcerer',
    palette: { bg1: '#100818', bg2: '#201030', accent: '#a040e0', glow: '#c060ff' },
    scene: `
      <!-- Wild magic sparks -->
      ${Array.from({length: 8}, (_, i) => `<circle cx="${40+i*18}" cy="${60+Math.sin(i*1.5)*30}" r="${1+i%2}" fill="#c060ff" opacity="${0.1+i*0.03}"/>`).join('')}

      <g transform="translate(100,78)">
        <path d="M-16,20 Q-18,14 -12,10 L-5,7 Q0,6 5,7 L12,10 Q18,14 16,20" fill="#2a1040" stroke="#a040e0" stroke-width="0.3"/>
        <path d="M-10,20 L-12,68 Q0,72 12,68 L10,20" fill="#1a0830" stroke="#4a2a5a" stroke-width="0.3"/>
        <!-- Magic crackling on robes -->
        <path d="M-8,35 Q-3,30 2,38 Q7,42 10,35" stroke="#c060ff" stroke-width="0.5" fill="none" opacity="0.3"/>
        <rect x="-3" y="3" width="6" height="7" fill="#c0a090" opacity="0.8"/>
        <ellipse cx="0" cy="-7" rx="12" ry="13" fill="#c0a090"/>
        <!-- Wild/dramatic hair -->
        <path d="M-12,-7 Q-14,-20 -8,-26 Q0,-32 8,-26 Q14,-20 12,-7" fill="#1a0520"/>
        <!-- Hair floating with magic -->
        <path d="M-12,-4 Q-18,-10 -20,-20" stroke="#1a0520" stroke-width="2.5" fill="none"/>
        <path d="M12,-4 Q18,-10 20,-20" stroke="#1a0520" stroke-width="2.5" fill="none"/>
        <!-- Glowing eyes -->
        <ellipse cx="-5" cy="-7" rx="2.5" ry="2" fill="#c060ff" opacity="0.8"/>
        <ellipse cx="5" cy="-7" rx="2.5" ry="2" fill="#c060ff" opacity="0.8"/>
        <circle cx="-5" cy="-7" r="0.7" fill="white" opacity="0.5"/>
        <circle cx="5" cy="-7" r="0.7" fill="white" opacity="0.5"/>
        <path d="M-3,0 Q0,1 3,0" stroke="#9a7a5a" stroke-width="0.5" fill="none"/>
        <!-- MAGIC HANDS — energy crackling -->
        <circle cx="-20" cy="30" r="4" fill="#c0a090"/>
        <circle cx="-20" cy="30" r="10" fill="#a040e0" opacity="0.08"/>
        <circle cx="-20" cy="30" r="6" fill="#c060ff" opacity="0.06"/>
        <circle cx="20" cy="25" r="4" fill="#c0a090"/>
        <circle cx="20" cy="25" r="10" fill="#a040e0" opacity="0.08"/>
        <!-- Energy arc between hands -->
        <path d="M-16,30 Q0,15 16,25" stroke="#c060ff" stroke-width="0.8" fill="none" opacity="0.4"/>
      </g>
    `,
  },
  {
    id: 'warlock',
    name: 'Warlock',
    palette: { bg1: '#0a0510', bg2: '#1a1020', accent: '#40c080', glow: '#60e0a0' },
    scene: `
      <!-- Eldritch eye in background -->
      <ellipse cx="100" cy="60" rx="30" ry="15" fill="none" stroke="#40c080" stroke-width="0.5" opacity="0.15"/>
      <ellipse cx="100" cy="60" rx="10" ry="12" fill="#40c080" opacity="0.05"/>
      <circle cx="100" cy="60" r="4" fill="#40c080" opacity="0.08"/>

      <g transform="translate(100,82)">
        <!-- Dark robes -->
        <path d="M-16,18 Q-18,12 -12,8 L-5,5 Q0,4 5,5 L12,8 Q18,12 16,18" fill="#1a1020" stroke="#40c080" stroke-width="0.3"/>
        <path d="M-10,18 L-14,68 Q0,74 14,68 L10,18" fill="#0a0510" stroke="#2a2a3a" stroke-width="0.3"/>
        <!-- Eldritch runes on robe hem -->
        ${[-8,-3,2,7].map(x => `<circle cx="${x}" cy="62" r="1.5" fill="#40c080" opacity="0.2"/>`).join('')}
        <rect x="-3" y="2" width="6" height="7" fill="#b8a888" opacity="0.8"/>
        <ellipse cx="0" cy="-7" rx="11" ry="13" fill="#b8a888"/>
        <path d="M-11,-7 Q-12,-18 -6,-22 Q0,-25 6,-22 Q12,-18 11,-7" fill="#1a0a10"/>
        <!-- Gaunt, intense features -->
        <ellipse cx="-4" cy="-7" rx="2" ry="2" fill="#40c080" opacity="0.7"/>
        <ellipse cx="4" cy="-7" rx="2" ry="2" fill="#40c080" opacity="0.7"/>
        <circle cx="-4" cy="-7" r="0.6" fill="#1a1020"/>
        <circle cx="4" cy="-7" r="0.6" fill="#1a1020"/>
        <path d="M-3,0 Q0,1 3,0" stroke="#8a7a5a" stroke-width="0.4" fill="none"/>
        <!-- PACT TOME -->
        <g transform="translate(-20,18) rotate(-10)">
          <rect x="-6" y="-8" width="12" height="16" fill="#1a1020" stroke="#40c080" stroke-width="0.5" rx="1"/>
          <circle cx="0" cy="0" r="3" fill="#40c080" opacity="0.3"/>
          <circle cx="0" cy="0" r="1" fill="#40c080" opacity="0.5"/>
        </g>
        <!-- Eldritch blast hand -->
        <circle cx="18" cy="28" r="4" fill="#b8a888"/>
        <circle cx="18" cy="28" r="8" fill="#40c080" opacity="0.08"/>
        <path d="M22,28 L35,20" stroke="#40c080" stroke-width="1" opacity="0.3"/>
        <path d="M22,26 L38,15" stroke="#40c080" stroke-width="0.5" opacity="0.2"/>
      </g>
    `,
  },
  {
    id: 'wizard',
    name: 'Wizard',
    palette: { bg1: '#08081a', bg2: '#151530', accent: '#4080e0', glow: '#60a0ff' },
    scene: `
      <!-- Arcane circle -->
      <circle cx="100" cy="140" r="35" fill="none" stroke="#4080e0" stroke-width="0.3" opacity="0.15"/>
      <circle cx="100" cy="140" r="25" fill="none" stroke="#4080e0" stroke-width="0.3" opacity="0.1"/>
      ${[0,60,120,180,240,300].map(a => {
        const r = 35, cx = 100 + r * Math.cos(a * Math.PI/180), cy = 140 + r * Math.sin(a * Math.PI/180);
        return `<circle cx="${cx.toFixed(1)}" cy="${cy.toFixed(1)}" r="1.5" fill="#4080e0" opacity="0.15"/>`;
      }).join('')}

      <g transform="translate(100,80)">
        <!-- Wizard robes — flowing -->
        <path d="M-16,18 Q-18,12 -12,8 L-5,5 Q0,4 5,5 L12,8 Q18,12 16,18" fill="#1a1a3a" stroke="#4080e0" stroke-width="0.3"/>
        <path d="M-12,18 L-16,68 Q0,74 16,68 L12,18" fill="#101030" stroke="#2a2a5a" stroke-width="0.3"/>
        <!-- Stars on robe -->
        ${[{x:-5,y:35},{x:4,y:45},{x:-3,y:55}].map(p => `<circle cx="${p.x}" cy="${p.y}" r="1" fill="#4080e0" opacity="0.3"/>`).join('')}
        <rect x="-3" y="2" width="6" height="7" fill="#b8a888" opacity="0.8"/>
        <ellipse cx="0" cy="-6" rx="11" ry="13" fill="#b8a888"/>
        <!-- POINTY HAT -->
        <path d="M-14,-4 Q-16,-14 -10,-20 Q0,-24 10,-20 Q16,-14 14,-4" fill="#1a1a4a" stroke="#4080e0" stroke-width="0.3"/>
        <path d="M-12,-16 Q-8,-30 0,-45 Q8,-30 12,-16" fill="#1a1a4a" stroke="#4080e0" stroke-width="0.3"/>
        <!-- Star on hat -->
        <circle cx="0" cy="-35" r="2" fill="#4080e0" opacity="0.5"/>
        <!-- Wise eyes -->
        <ellipse cx="-4" cy="-5" rx="2" ry="1.5" fill="#4080e0" opacity="0.6"/>
        <ellipse cx="4" cy="-5" rx="2" ry="1.5" fill="#4080e0" opacity="0.6"/>
        <!-- Long beard -->
        <path d="M-8,-1 Q-10,10 -6,25 Q-2,32 0,35 Q2,32 6,25 Q10,10 8,-1" fill="#b0a890" opacity="0.8"/>
        <path d="M-4,5 Q0,15 0,30" stroke="#c0b8a0" stroke-width="0.3" fill="none"/>
        <!-- STAFF with orb -->
        <rect x="18" y="-35" width="3" height="85" fill="#5a4a3a" rx="1"/>
        <circle cx="19.5" cy="-38" r="6" fill="#4080e0" opacity="0.15"/>
        <circle cx="19.5" cy="-38" r="4" fill="#60a0ff" opacity="0.2"/>
        <circle cx="19.5" cy="-38" r="2" fill="#80c0ff" opacity="0.3"/>
        <!-- Open spellbook -->
        <g transform="translate(-22,25) rotate(-5)">
          <rect x="-8" y="-5" width="16" height="10" fill="#c0b890" stroke="#4080e0" stroke-width="0.3" rx="1"/>
          <line x1="0" y1="-5" x2="0" y2="5" stroke="#4080e0" stroke-width="0.3"/>
          ${[-5,-3,-1,1,3,5].map(x => `<line x1="${x}" y1="-2" x2="${x+1.5}" y2="-2" stroke="#2a2a4a" stroke-width="0.3" opacity="0.4"/>`).join('')}
        </g>
      </g>
    `,
  },
];

test.describe('Class Art Generation', () => {
  for (const cls of CLASSES) {
    test(`Generate: ${cls.name}`, async ({ browser }) => {
      const ctx = await browser.newContext({ viewport: { width: 200, height: 260 } });
      const page = await ctx.newPage();

      const svg = `
        <svg xmlns="http://www.w3.org/2000/svg" width="200" height="260" viewBox="0 0 200 260">
          <defs>
            <linearGradient id="bg" x1="0" y1="0" x2="0.3" y2="1">
              <stop offset="0%" stop-color="${cls.palette.bg1}"/>
              <stop offset="100%" stop-color="${cls.palette.bg2}"/>
            </linearGradient>
            <radialGradient id="glow" cx="0.5" cy="0.4" r="0.5">
              <stop offset="0%" stop-color="${cls.palette.glow}" stop-opacity="0.12"/>
              <stop offset="100%" stop-color="${cls.palette.bg1}" stop-opacity="0"/>
            </radialGradient>
          </defs>
          <rect width="200" height="260" fill="url(#bg)"/>
          <rect width="200" height="260" fill="url(#glow)"/>
          ${cls.scene}
          <rect x="0" y="215" width="200" height="45" fill="${cls.palette.bg1}" opacity="0.85"/>
          <line x1="10" y1="220" x2="190" y2="220" stroke="${cls.palette.accent}" stroke-width="0.5" opacity="0.5"/>
          <text x="100" y="244" text-anchor="middle" font-family="Georgia, 'Times New Roman', serif" font-size="16" font-weight="bold" fill="${cls.palette.accent}" letter-spacing="2">${cls.name.toUpperCase()}</text>
          <rect x="0" y="0" width="200" height="260" fill="none" stroke="${cls.palette.accent}" stroke-width="0.5" opacity="0.3" rx="4"/>
        </svg>
      `;

      await page.setContent(`<html><head><style>*{margin:0;padding:0;}body{width:200px;height:260px;overflow:hidden;}</style></head><body>${svg}</body></html>`);
      await page.screenshot({ path: `../../public/art/classes/${cls.id}.png`, clip: { x: 0, y: 0, width: 200, height: 260 } });
      await ctx.close();
    });
  }
});
