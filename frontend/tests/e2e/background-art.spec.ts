/**
 * Generate D&D background art — atmospheric scene icons, 160x160.
 */
import { test } from '@playwright/test';

interface BgArt {
  id: string;
  name: string;
  palette: { bg1: string; bg2: string; accent: string; glow: string };
  scene: string;
}

const BACKGROUNDS: BgArt[] = [
  {
    id: 'acolyte', name: 'Acolyte',
    palette: { bg1: '#101018', bg2: '#1a1a2a', accent: '#e0c040', glow: '#ffe060' },
    scene: `
      <path d="M60,20 L70,70 L90,70 L100,20" fill="#e0c040" opacity="0.04"/>
      <rect x="68" y="50" width="24" height="40" fill="#1a1a2a" stroke="#e0c040" stroke-width="0.5" opacity="0.6"/>
      <polygon points="68,50 80,35 92,50" fill="#1a1a2a" stroke="#e0c040" stroke-width="0.5" opacity="0.6"/>
      <circle cx="80" cy="44" r="3" fill="#e0c040" opacity="0.3"/>
      <line x1="80" y1="55" x2="80" y2="75" stroke="#e0c040" stroke-width="0.8" opacity="0.4"/>
      <line x1="72" y1="65" x2="88" y2="65" stroke="#e0c040" stroke-width="0.8" opacity="0.4"/>
      <rect x="65" y="90" width="30" height="8" fill="#2a2a3a" stroke="#e0c040" stroke-width="0.3" rx="1"/>
    `,
  },
  {
    id: 'charlatan', name: 'Charlatan',
    palette: { bg1: '#1a0a18', bg2: '#2a1528', accent: '#d060a0', glow: '#e080c0' },
    scene: `
      <!-- Cards and dice -->
      <g transform="translate(80,45) rotate(-10)">
        <rect x="-12" y="-18" width="24" height="36" fill="#2a1528" stroke="#d060a0" stroke-width="0.5" rx="2"/>
        <circle cx="0" cy="0" r="4" fill="#d060a0" opacity="0.3"/>
      </g>
      <g transform="translate(88,50) rotate(8)">
        <rect x="-12" y="-18" width="24" height="36" fill="#2a1528" stroke="#d060a0" stroke-width="0.5" rx="2"/>
        <text x="0" y="5" text-anchor="middle" font-size="14" fill="#d060a0" opacity="0.5">♠</text>
      </g>
      <circle cx="65" cy="85" r="5" fill="#2a1528" stroke="#d060a0" stroke-width="0.5"/>
      <circle cx="65" cy="85" r="1" fill="#d060a0" opacity="0.4"/>
      <circle cx="95" cy="82" r="5" fill="#2a1528" stroke="#d060a0" stroke-width="0.5"/>
    `,
  },
  {
    id: 'criminal', name: 'Criminal',
    palette: { bg1: '#0a0810', bg2: '#1a1520', accent: '#8070a0', glow: '#a090c0' },
    scene: `
      <rect x="55" y="40" width="50" height="40" fill="#1a1520" stroke="#8070a0" stroke-width="0.5" opacity="0.5" rx="2"/>
      <circle cx="80" cy="52" r="6" fill="none" stroke="#8070a0" stroke-width="1" opacity="0.5"/>
      <circle cx="80" cy="52" r="2" fill="#8070a0" opacity="0.3"/>
      <rect x="65" y="85" width="30" height="3" fill="#8070a0" opacity="0.2"/>
      <path d="M70,40 Q72,30 80,28 Q88,30 90,40" stroke="#8070a0" stroke-width="0.5" fill="none" opacity="0.3"/>
      <path d="M60,95 L65,88 L70,95" stroke="#5a4a6a" stroke-width="1" fill="none" opacity="0.4"/>
      <path d="M90,95 L95,88 L100,95" stroke="#5a4a6a" stroke-width="1" fill="none" opacity="0.4"/>
    `,
  },
  {
    id: 'entertainer', name: 'Entertainer',
    palette: { bg1: '#1a0a10', bg2: '#2a1520', accent: '#e06080', glow: '#ff80a0' },
    scene: `
      <!-- Stage/curtains -->
      <path d="M30,20 Q40,30 35,60 L30,100" stroke="#e06080" stroke-width="1.5" fill="none" opacity="0.3"/>
      <path d="M130,20 Q120,30 125,60 L130,100" stroke="#e06080" stroke-width="1.5" fill="none" opacity="0.3"/>
      <!-- Mask -->
      <g transform="translate(80,55)">
        <ellipse cx="0" cy="0" rx="18" ry="22" fill="#2a1520" stroke="#e06080" stroke-width="0.8"/>
        <ellipse cx="-6" cy="-5" rx="4" ry="3" fill="#1a0a10"/>
        <ellipse cx="6" cy="-5" rx="4" ry="3" fill="#1a0a10"/>
        <path d="M-6,6 Q0,12 6,6" stroke="#e06080" stroke-width="0.8" fill="none"/>
      </g>
      <!-- Spotlight -->
      <circle cx="80" cy="55" r="28" fill="#e06080" opacity="0.04"/>
    `,
  },
  {
    id: 'folk-hero', name: 'Folk Hero',
    palette: { bg1: '#101008', bg2: '#2a2810', accent: '#c0a040', glow: '#e0c060' },
    scene: `
      <!-- Pitchfork/farming tool -->
      <rect x="78" y="25" width="4" height="55" fill="#6a5a3a"/>
      <path d="M72,25 L80,15 L88,25" fill="none" stroke="#c0a040" stroke-width="1.5"/>
      <line x1="74" y1="25" x2="74" y2="35" stroke="#6a5a3a" stroke-width="1.5"/>
      <line x1="86" y1="25" x2="86" y2="35" stroke="#6a5a3a" stroke-width="1.5"/>
      <!-- Wheat/crops -->
      ${[55,65,95,105].map((x, i) => `<line x1="${x}" y1="100" x2="${x+2}" y2="${80-i*3}" stroke="#c0a040" stroke-width="0.8" opacity="${0.3+i*0.05}"/>`).join('')}
      <!-- Sun -->
      <circle cx="80" cy="90" r="10" fill="#c0a040" opacity="0.08"/>
    `,
  },
  {
    id: 'guild-artisan', name: 'Guild Artisan',
    palette: { bg1: '#1a1008', bg2: '#2a1a0a', accent: '#e08030', glow: '#ff9940' },
    scene: `
      <!-- Anvil -->
      <path d="M60,70 L65,55 L95,55 L100,70 L105,75 L55,75 Z" fill="#3a3a3a" stroke="#e08030" stroke-width="0.5"/>
      <!-- Hammer -->
      <rect x="76" y="30" width="4" height="28" fill="#6a5a3a" transform="rotate(-15,78,44)"/>
      <rect x="70" y="25" width="16" height="8" fill="#5a5a5a" stroke="#e08030" stroke-width="0.3" rx="1" transform="rotate(-15,78,29)"/>
      <!-- Sparks -->
      ${Array.from({length: 5}, (_, i) => `<circle cx="${70+i*5}" cy="${50+Math.sin(i)*5}" r="1" fill="#e08030" opacity="${0.3+i*0.1}"/>`).join('')}
      <!-- Guild seal -->
      <circle cx="80" cy="92" r="8" fill="none" stroke="#e08030" stroke-width="0.8" opacity="0.3"/>
    `,
  },
  {
    id: 'hermit', name: 'Hermit',
    palette: { bg1: '#081008', bg2: '#142014', accent: '#60a060', glow: '#80c080' },
    scene: `
      <!-- Cave/nature -->
      <path d="M30,40 Q80,10 130,40 L130,100 L30,100 Z" fill="#0a1508" stroke="#60a060" stroke-width="0.3" opacity="0.4"/>
      <!-- Herbs/plants -->
      ${[50,70,90,110].map((x, i) => `<path d="M${x},95 Q${x+2},${85-i*2} ${x+4},95" stroke="#60a060" stroke-width="0.8" fill="none" opacity="${0.3+i*0.05}"/>`).join('')}
      <!-- Potion bottle -->
      <rect x="75" y="55" width="10" height="15" fill="#142014" stroke="#60a060" stroke-width="0.5" rx="2"/>
      <rect x="77" y="50" width="6" height="6" fill="#142014" stroke="#60a060" stroke-width="0.3"/>
      <rect x="77" y="60" width="6" height="8" fill="#60a060" opacity="0.15" rx="1"/>
    `,
  },
  {
    id: 'noble', name: 'Noble',
    palette: { bg1: '#10081a', bg2: '#201530', accent: '#c080e0', glow: '#d0a0f0' },
    scene: `
      <!-- Crown -->
      <g transform="translate(80,40)">
        <path d="M-15,10 L-12,0 L-6,8 L0,-5 L6,8 L12,0 L15,10 Z" fill="#c080e0" opacity="0.5" stroke="#c080e0" stroke-width="0.5"/>
        <rect x="-15" y="10" width="30" height="6" fill="#201530" stroke="#c080e0" stroke-width="0.5"/>
        <circle cx="-6" cy="13" r="1.5" fill="#c080e0" opacity="0.4"/>
        <circle cx="0" cy="13" r="1.5" fill="#c080e0" opacity="0.4"/>
        <circle cx="6" cy="13" r="1.5" fill="#c080e0" opacity="0.4"/>
      </g>
      <!-- Signet ring -->
      <circle cx="80" cy="75" r="8" fill="none" stroke="#c080e0" stroke-width="0.8" opacity="0.3"/>
      <circle cx="80" cy="75" r="3" fill="#c080e0" opacity="0.15"/>
      <!-- Scroll/decree -->
      <rect x="60" y="88" width="40" height="6" fill="#201530" stroke="#c080e0" stroke-width="0.3" rx="3"/>
    `,
  },
  {
    id: 'sage', name: 'Sage',
    palette: { bg1: '#08081a', bg2: '#151530', accent: '#4080e0', glow: '#60a0ff' },
    scene: `
      <!-- Open book -->
      <g transform="translate(80,50)">
        <rect x="-20" y="-12" width="18" height="24" fill="#151530" stroke="#4080e0" stroke-width="0.5" rx="1"/>
        <rect x="2" y="-12" width="18" height="24" fill="#151530" stroke="#4080e0" stroke-width="0.5" rx="1"/>
        <line x1="0" y1="-12" x2="0" y2="12" stroke="#4080e0" stroke-width="0.3"/>
        ${[-14,-10,-6,4,8,12].map(x => `<line x1="${x}" y1="-6" x2="${x+3}" y2="-6" stroke="#4080e0" stroke-width="0.3" opacity="0.3"/>`).join('')}
        ${[-14,-10,-6,4,8,12].map(x => `<line x1="${x}" y1="0" x2="${x+3}" y2="0" stroke="#4080e0" stroke-width="0.3" opacity="0.3"/>`).join('')}
      </g>
      <!-- Quill -->
      <path d="M105,35 L110,55 L108,56 L103,37" fill="#4080e0" opacity="0.4"/>
      <!-- Ink pot -->
      <rect x="50" y="70" width="8" height="8" fill="#151530" stroke="#4080e0" stroke-width="0.5" rx="1"/>
    `,
  },
  {
    id: 'sailor', name: 'Sailor',
    palette: { bg1: '#081520', bg2: '#0a2030', accent: '#3090c0', glow: '#50b0e0' },
    scene: `
      <!-- Waves -->
      ${[0,1,2].map(i => `<path d="M20,${80+i*10} Q50,${72+i*10} 80,${80+i*10} Q110,${88+i*10} 140,${80+i*10}" stroke="#3090c0" stroke-width="0.8" fill="none" opacity="${0.2-i*0.05}"/>`).join('')}
      <!-- Ship wheel -->
      <circle cx="80" cy="48" r="16" fill="none" stroke="#3090c0" stroke-width="1" opacity="0.4"/>
      <circle cx="80" cy="48" r="4" fill="#3090c0" opacity="0.15"/>
      ${[0,45,90,135,180,225,270,315].map(a => {
        const x1 = 80 + 4 * Math.cos(a * Math.PI/180), y1 = 48 + 4 * Math.sin(a * Math.PI/180);
        const x2 = 80 + 16 * Math.cos(a * Math.PI/180), y2 = 48 + 16 * Math.sin(a * Math.PI/180);
        return `<line x1="${x1.toFixed(1)}" y1="${y1.toFixed(1)}" x2="${x2.toFixed(1)}" y2="${y2.toFixed(1)}" stroke="#3090c0" stroke-width="0.5" opacity="0.3"/>`;
      }).join('')}
      <!-- Anchor -->
      <line x1="80" y1="70" x2="80" y2="90" stroke="#3090c0" stroke-width="1" opacity="0.3"/>
      <path d="M70,85 Q80,95 90,85" stroke="#3090c0" stroke-width="1" fill="none" opacity="0.3"/>
    `,
  },
  {
    id: 'soldier', name: 'Soldier',
    palette: { bg1: '#101015', bg2: '#1a1a22', accent: '#8090b0', glow: '#a0b0d0' },
    scene: `
      <!-- Sword left -->
      <line x1="60" y1="25" x2="90" y2="75" stroke="#8090b0" stroke-width="2" opacity="0.4"/>
      <line x1="55" y1="32" x2="65" y2="28" stroke="#8090b0" stroke-width="1.5" opacity="0.3"/>
      <!-- Sword right -->
      <line x1="100" y1="25" x2="70" y2="75" stroke="#8090b0" stroke-width="2" opacity="0.4"/>
      <line x1="95" y1="28" x2="105" y2="32" stroke="#8090b0" stroke-width="1.5" opacity="0.3"/>
      <!-- Shield -->
      <path d="M68,75 L80,70 L92,75 L92,92 L80,98 L68,92 Z" fill="#1a1a2a" stroke="#8090b0" stroke-width="0.8" opacity="0.4"/>
      <line x1="80" y1="73" x2="80" y2="95" stroke="#8090b0" stroke-width="0.5" opacity="0.3"/>
    `,
  },
  {
    id: 'urchin', name: 'Urchin',
    palette: { bg1: '#101010', bg2: '#1a1a1a', accent: '#a09080', glow: '#c0b0a0' },
    scene: `
      <!-- City alley -->
      <rect x="30" y="30" width="15" height="70" fill="#1a1a1a" stroke="#a09080" stroke-width="0.3" opacity="0.4"/>
      <rect x="115" y="25" width="15" height="75" fill="#1a1a1a" stroke="#a09080" stroke-width="0.3" opacity="0.4"/>
      <!-- Small figure silhouette -->
      <g transform="translate(80,60)" opacity="0.5">
        <circle cx="0" cy="-10" r="6" fill="#a09080" opacity="0.3"/>
        <rect x="-5" y="-4" width="10" height="18" fill="#a09080" opacity="0.2" rx="2"/>
      </g>
      <!-- Scattered coins -->
      ${[55,70,85,100].map((x, i) => `<circle cx="${x}" cy="${88+i*2}" r="2" fill="#a09080" opacity="${0.2+i*0.05}"/>`).join('')}
      <!-- Rat -->
      <ellipse cx="105" cy="95" rx="4" ry="2.5" fill="#a09080" opacity="0.2"/>
      <path d="M109,95 Q115,93 118,95" stroke="#a09080" stroke-width="0.3" fill="none" opacity="0.2"/>
    `,
  },
];

test.describe('Background Art Generation', () => {
  for (const bg of BACKGROUNDS) {
    test(`Generate: ${bg.name}`, async ({ browser }) => {
      const ctx = await browser.newContext({ viewport: { width: 160, height: 160 } });
      const page = await ctx.newPage();

      const svg = `
        <svg xmlns="http://www.w3.org/2000/svg" width="160" height="160" viewBox="0 0 160 160">
          <defs>
            <linearGradient id="bg" x1="0" y1="0" x2="0.3" y2="1">
              <stop offset="0%" stop-color="${bg.palette.bg1}"/>
              <stop offset="100%" stop-color="${bg.palette.bg2}"/>
            </linearGradient>
            <radialGradient id="glow" cx="0.5" cy="0.4" r="0.5">
              <stop offset="0%" stop-color="${bg.palette.glow}" stop-opacity="0.1"/>
              <stop offset="100%" stop-color="${bg.palette.bg1}" stop-opacity="0"/>
            </radialGradient>
          </defs>
          <rect width="160" height="160" fill="url(#bg)"/>
          <rect width="160" height="160" fill="url(#glow)"/>
          ${bg.scene}
          <rect x="0" y="118" width="160" height="42" fill="${bg.palette.bg1}" opacity="0.85"/>
          <line x1="10" y1="122" x2="150" y2="122" stroke="${bg.palette.accent}" stroke-width="0.5" opacity="0.4"/>
          <text x="80" y="144" text-anchor="middle" font-family="Georgia, 'Times New Roman', serif" font-size="13" font-weight="bold" fill="${bg.palette.accent}" letter-spacing="1.5">${bg.name.toUpperCase()}</text>
          <rect x="0" y="0" width="160" height="160" fill="none" stroke="${bg.palette.accent}" stroke-width="0.5" opacity="0.2" rx="4"/>
        </svg>
      `;

      await page.setContent(`<html><head><style>*{margin:0;padding:0;}body{width:160px;height:160px;overflow:hidden;}</style></head><body>${svg}</body></html>`);
      await page.screenshot({ path: `./public/art/backgrounds/${bg.id}.png`, clip: { x: 0, y: 0, width: 160, height: 160 } });
      await ctx.close();
    });
  }
});
