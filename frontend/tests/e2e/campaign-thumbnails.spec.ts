/**
 * Generate campaign thumbnail images — atmospheric SVG scenes rendered to PNG.
 * Each thumbnail is 600×340 (16:9-ish card ratio) with a dark fantasy art style.
 */
import { test } from '@playwright/test';

interface CampaignArt {
  id: string;
  title: string;
  palette: { bg1: string; bg2: string; accent: string; glow: string; text: string };
  scene: string; // SVG scene elements
}

const CAMPAIGNS: CampaignArt[] = [
  {
    id: 'wrath-of-the-stormspire',
    title: 'Wrath of the Stormspire',
    palette: { bg1: '#0a0a20', bg2: '#1a1040', accent: '#7b68ee', glow: '#9370db', text: '#e8d5ff' },
    scene: `
      <!-- Cloud sea -->
      <ellipse cx="300" cy="320" rx="500" ry="60" fill="url(#clouds)" opacity="0.7"/>
      <ellipse cx="200" cy="330" rx="300" ry="40" fill="url(#clouds)" opacity="0.5"/>
      <ellipse cx="450" cy="310" rx="250" ry="35" fill="url(#clouds)" opacity="0.6"/>

      <!-- Mountain/Stormspire -->
      <polygon points="300,40 220,280 380,280" fill="url(#mountain)"/>
      <polygon points="300,40 260,160 340,160" fill="#2a2050" opacity="0.5"/>

      <!-- Bastion at peak -->
      <rect x="275" y="50" width="50" height="35" fill="#3a2a5a" stroke="#7b68ee" stroke-width="1"/>
      <polygon points="270,50 300,30 330,50" fill="#4a3a6a" stroke="#7b68ee" stroke-width="1"/>
      <rect x="285" y="60" width="8" height="12" fill="#9370db" opacity="0.8"/>
      <rect x="305" y="60" width="8" height="12" fill="#9370db" opacity="0.6"/>
      <!-- Spire towers -->
      <rect x="268" y="42" width="8" height="20" fill="#3a2a5a"/>
      <polygon points="268,42 272,32 276,42" fill="#4a3a6a"/>
      <rect x="324" y="42" width="8" height="20" fill="#3a2a5a"/>
      <polygon points="324,42 328,32 332,42" fill="#4a3a6a"/>

      <!-- Lightning bolts -->
      <polyline points="180,20 190,80 175,85 195,150" stroke="#b088ff" stroke-width="2.5" fill="none" opacity="0.9"/>
      <polyline points="420,40 415,110 430,115 410,180" stroke="#9370db" stroke-width="2" fill="none" opacity="0.7"/>
      <polyline points="500,10 490,60 505,65 485,120" stroke="#7b68ee" stroke-width="1.5" fill="none" opacity="0.5"/>

      <!-- Griffon silhouettes -->
      <g transform="translate(130,90) scale(0.4)" opacity="0.6">
        <path d="M0,0 Q10,-15 25,-10 L35,-5 Q40,0 35,5 L20,8 Q10,10 5,5 Z" fill="#2a1a4a"/>
        <path d="M25,-10 Q40,-25 55,-15 L45,-5" fill="none" stroke="#2a1a4a" stroke-width="3"/>
        <path d="M5,5 Q-10,15 -20,10 L-5,2" fill="none" stroke="#2a1a4a" stroke-width="3"/>
      </g>
      <g transform="translate(440,70) scale(0.3) scaleX(-1)" opacity="0.4">
        <path d="M0,0 Q10,-15 25,-10 L35,-5 Q40,0 35,5 L20,8 Q10,10 5,5 Z" fill="#2a1a4a"/>
        <path d="M25,-10 Q40,-25 55,-15 L45,-5" fill="none" stroke="#2a1a4a" stroke-width="3"/>
      </g>

      <!-- Storm particles -->
      ${Array.from({length: 20}, (_, i) => {
        const x = 50 + Math.sin(i * 1.7) * 250 + 250;
        const y = 30 + (i * 14) % 250;
        const r = 1 + (i % 3);
        return `<circle cx="${x}" cy="${y}" r="${r}" fill="#b088ff" opacity="${0.2 + (i % 5) * 0.1}"/>`;
      }).join('\n      ')}

      <defs>
        <linearGradient id="clouds" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stop-color="#4a3a6a" stop-opacity="0.6"/>
          <stop offset="100%" stop-color="#2a1a4a" stop-opacity="0.2"/>
        </linearGradient>
        <linearGradient id="mountain" x1="0.5" y1="0" x2="0.5" y2="1">
          <stop offset="0%" stop-color="#3a2a5a"/>
          <stop offset="100%" stop-color="#1a1030"/>
        </linearGradient>
      </defs>
    `,
  },
  {
    id: 'the-drowned-throne',
    title: 'The Drowned Throne',
    palette: { bg1: '#020a15', bg2: '#0a2030', accent: '#1a8a7a', glow: '#20b0a0', text: '#b0e8e0' },
    scene: `
      <!-- Water surface -->
      <rect x="0" y="0" width="600" height="160" fill="url(#waterTop)" opacity="0.3"/>

      <!-- Underwater glow -->
      <circle cx="300" cy="280" r="120" fill="#0a4040" opacity="0.4"/>
      <circle cx="300" cy="280" r="80" fill="#105050" opacity="0.3"/>

      <!-- Sunken city ruins -->
      <rect x="180" y="180" width="40" height="80" fill="#0a3030" stroke="#1a6a5a" stroke-width="0.5" opacity="0.7" transform="rotate(-5,200,220)"/>
      <rect x="240" y="160" width="50" height="100" fill="#0a3535" stroke="#1a7a6a" stroke-width="0.5" opacity="0.8"/>
      <polygon points="240,160 265,140 290,160" fill="#0a4040" stroke="#1a7a6a" stroke-width="0.5"/>
      <rect x="330" y="170" width="45" height="90" fill="#0a3030" stroke="#1a6a5a" stroke-width="0.5" opacity="0.7" transform="rotate(3,352,215)"/>
      <rect x="400" y="190" width="35" height="70" fill="#082828" stroke="#1a5a5a" stroke-width="0.5" opacity="0.6" transform="rotate(8,417,225)"/>

      <!-- Drowned Throne -->
      <rect x="260" y="210" width="80" height="60" fill="#0a4545" stroke="#20b0a0" stroke-width="1"/>
      <rect x="270" y="195" width="60" height="20" fill="#0a4a4a" stroke="#20b0a0" stroke-width="1"/>
      <polygon points="270,195 300,175 330,195" fill="#0a5050" stroke="#20b0a0" stroke-width="1"/>
      <!-- Throne glow -->
      <rect x="288" y="225" width="24" height="30" fill="#20b0a0" opacity="0.3"/>
      <circle cx="300" cy="240" r="8" fill="#20b0a0" opacity="0.5"/>
      <circle cx="300" cy="240" r="4" fill="#40d0c0" opacity="0.7"/>

      <!-- Kelp/seaweed -->
      ${[140, 200, 380, 450, 510].map((x, i) => `
        <path d="M${x},340 Q${x + 5},${280 - i*10} ${x - 5},${220 - i*8} Q${x + 8},${180 - i*5} ${x},${160 - i*12}" stroke="#0a5a3a" stroke-width="3" fill="none" opacity="${0.3 + i*0.08}"/>
      `).join('')}

      <!-- Bubbles -->
      ${Array.from({length: 15}, (_, i) => {
        const x = 100 + (i * 37) % 400;
        const y = 60 + (i * 23) % 240;
        const r = 2 + (i % 4);
        return `<circle cx="${x}" cy="${y}" r="${r}" fill="none" stroke="#20b0a0" stroke-width="0.5" opacity="${0.2 + (i%4)*0.1}"/>`;
      }).join('\n      ')}

      <!-- Pale figures -->
      <g opacity="0.25">
        <ellipse cx="170" cy="250" rx="8" ry="18" fill="#60c0b0"/>
        <ellipse cx="430" cy="230" rx="7" ry="16" fill="#60c0b0"/>
        <ellipse cx="350" cy="270" rx="6" ry="14" fill="#60c0b0"/>
      </g>

      <defs>
        <linearGradient id="waterTop" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stop-color="#1a8a7a" stop-opacity="0.2"/>
          <stop offset="100%" stop-color="#020a15" stop-opacity="0"/>
        </linearGradient>
      </defs>
    `,
  },
  {
    id: 'ember-of-the-last-god',
    title: 'Ember of the Last God',
    palette: { bg1: '#1a0a00', bg2: '#2a1000', accent: '#ff6a20', glow: '#ff8844', text: '#ffe0c0' },
    scene: `
      <!-- Ashfield ground -->
      <rect x="0" y="230" width="600" height="110" fill="url(#ash)"/>

      <!-- God corpse silhouette (massive fallen figure on horizon) -->
      <g opacity="0.4">
        <ellipse cx="350" cy="230" rx="180" ry="25" fill="#2a1500"/>
        <path d="M200,230 Q220,180 260,190 Q280,170 300,195 Q330,160 350,190 Q380,175 400,200 Q440,185 480,230" fill="#2a1500"/>
        <!-- Ribcage shapes -->
        <path d="M280,210 Q290,190 300,210" stroke="#3a2000" stroke-width="2" fill="none"/>
        <path d="M310,205 Q320,185 330,205" stroke="#3a2000" stroke-width="2" fill="none"/>
        <path d="M340,208 Q350,188 360,208" stroke="#3a2000" stroke-width="2" fill="none"/>
      </g>

      <!-- Ember child (glowing figure) -->
      <g transform="translate(300,210)">
        <circle cx="0" cy="0" r="30" fill="#ff6a20" opacity="0.1"/>
        <circle cx="0" cy="0" r="18" fill="#ff8844" opacity="0.15"/>
        <circle cx="0" cy="0" r="8" fill="#ffaa44" opacity="0.25"/>
        <!-- Small figure silhouette -->
        <ellipse cx="0" cy="-2" rx="4" ry="8" fill="#ffcc66" opacity="0.6"/>
        <circle cx="0" cy="-12" r="3" fill="#ffcc66" opacity="0.6"/>
      </g>

      <!-- Smoke/ash pillars in background -->
      ${[80, 170, 430, 520].map((x, i) => `
        <path d="M${x},230 Q${x+10},${160-i*10} ${x-5},${80-i*15} Q${x+15},${20-i*5} ${x+5},0" stroke="#4a2a10" stroke-width="${4+i}" fill="none" opacity="${0.2+i*0.05}"/>
      `).join('')}

      <!-- Scattered embers/sparks -->
      ${Array.from({length: 25}, (_, i) => {
        const x = 40 + (i * 23) % 520;
        const y = 20 + (i * 17) % 200;
        const r = 1 + (i % 3) * 0.5;
        return `<circle cx="${x}" cy="${y}" r="${r}" fill="#ff${(6+i%4).toString(16)}a20" opacity="${0.3 + (i%5)*0.12}"/>`;
      }).join('\n      ')}

      <!-- Cracked ground lines -->
      <path d="M0,270 L80,265 L120,275 L200,260 L280,270 L350,262 L420,272 L500,265 L600,270" stroke="#4a2000" stroke-width="1" fill="none" opacity="0.5"/>
      <path d="M150,275 L150,310 L170,340" stroke="#3a1800" stroke-width="0.5" fill="none" opacity="0.4"/>
      <path d="M350,268 L360,300 L340,340" stroke="#3a1800" stroke-width="0.5" fill="none" opacity="0.4"/>

      <defs>
        <linearGradient id="ash" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stop-color="#3a1a00"/>
          <stop offset="100%" stop-color="#1a0a00"/>
        </linearGradient>
      </defs>
    `,
  },
  {
    id: 'carnival-of-stolen-faces',
    title: 'Carnival of Stolen Faces',
    palette: { bg1: '#0a0020', bg2: '#1a0a30', accent: '#e040a0', glow: '#ff60c0', text: '#ffd0f0' },
    scene: `
      <!-- Carnival tent (main) -->
      <polygon points="300,50 180,200 420,200" fill="url(#tent1)" stroke="#e040a0" stroke-width="1"/>
      <polygon points="300,50 240,200 360,200" fill="url(#tent2)" opacity="0.5"/>
      <!-- Tent stripes -->
      <line x1="300" y1="50" x2="210" y2="200" stroke="#ff60c0" stroke-width="0.5" opacity="0.3"/>
      <line x1="300" y1="50" x2="240" y2="200" stroke="#ff60c0" stroke-width="0.5" opacity="0.3"/>
      <line x1="300" y1="50" x2="270" y2="200" stroke="#ff60c0" stroke-width="0.5" opacity="0.3"/>
      <line x1="300" y1="50" x2="330" y2="200" stroke="#ff60c0" stroke-width="0.5" opacity="0.3"/>
      <line x1="300" y1="50" x2="360" y2="200" stroke="#ff60c0" stroke-width="0.5" opacity="0.3"/>
      <line x1="300" y1="50" x2="390" y2="200" stroke="#ff60c0" stroke-width="0.5" opacity="0.3"/>
      <!-- Tent flag -->
      <line x1="300" y1="30" x2="300" y2="55" stroke="#c030a0" stroke-width="1.5"/>
      <polygon points="300,30 320,38 300,46" fill="#e040a0"/>

      <!-- Side tents -->
      <polygon points="100,120 50,220 150,220" fill="#1a0a30" stroke="#a030a0" stroke-width="0.5" opacity="0.6"/>
      <polygon points="500,130 450,220 550,220" fill="#1a0a30" stroke="#a030a0" stroke-width="0.5" opacity="0.6"/>

      <!-- Ground/entrance -->
      <rect x="260" y="200" width="80" height="40" fill="#2a0a30" stroke="#e040a0" stroke-width="0.5"/>
      <rect x="280" y="200" width="40" height="35" fill="#0a0020" opacity="0.8"/>

      <!-- Floating masks -->
      ${[{x:130,y:80,r:12},{x:470,y:90,r:10},{x:80,y:160,r:9},{x:520,y:150,r:11},{x:220,y:40,r:8},{x:400,y:50,r:9}].map((m, i) => `
        <g transform="translate(${m.x},${m.y})" opacity="${0.4 + i*0.08}">
          <ellipse cx="0" cy="0" rx="${m.r}" ry="${m.r*1.2}" fill="#2a0a30" stroke="#e040a0" stroke-width="0.8"/>
          <ellipse cx="${-m.r*0.3}" cy="${-m.r*0.2}" rx="${m.r*0.2}" ry="${m.r*0.15}" fill="#0a0020"/>
          <ellipse cx="${m.r*0.3}" cy="${-m.r*0.2}" rx="${m.r*0.2}" ry="${m.r*0.15}" fill="#0a0020"/>
          <path d="M${-m.r*0.3},${m.r*0.3} Q0,${m.r*0.5} ${m.r*0.3},${m.r*0.3}" stroke="#e040a0" stroke-width="0.5" fill="none"/>
        </g>
      `).join('')}

      <!-- Stars/sparkles -->
      ${Array.from({length: 20}, (_, i) => {
        const x = 20 + (i * 31) % 560;
        const y = 10 + (i * 19) % 180;
        return `<circle cx="${x}" cy="${y}" r="${1 + i%2}" fill="#ff60c0" opacity="${0.15 + (i%5)*0.08}"/>`;
      }).join('\n      ')}

      <!-- String lights -->
      <path d="M50,100 Q150,85 200,95 Q250,105 300,90 Q350,80 400,95 Q450,108 550,95" stroke="#ffcc00" stroke-width="0.5" fill="none" opacity="0.4"/>
      ${[100,150,200,250,300,350,400,450,500].map((x, i) => 
        `<circle cx="${x}" cy="${88 + Math.sin(i*0.8)*8}" r="2" fill="${['#ffcc00','#ff60c0','#60ff60','#6060ff','#ffcc00'][i%5]}" opacity="0.6"/>`
      ).join('\n      ')}

      <defs>
        <linearGradient id="tent1" x1="0.5" y1="0" x2="0.5" y2="1">
          <stop offset="0%" stop-color="#4a1040"/>
          <stop offset="100%" stop-color="#2a0830"/>
        </linearGradient>
        <linearGradient id="tent2" x1="0.5" y1="0" x2="0.5" y2="1">
          <stop offset="0%" stop-color="#6a2060"/>
          <stop offset="100%" stop-color="#3a1040"/>
        </linearGradient>
      </defs>
    `,
  },
  {
    id: 'iron-oath-of-karak-dum',
    title: 'Iron Oath of Karak-Dum',
    palette: { bg1: '#1a0a00', bg2: '#2a1505', accent: '#ff4400', glow: '#ff6622', text: '#ffd0a0' },
    scene: `
      <!-- Volcano shape -->
      <polygon points="300,30 120,280 480,280" fill="url(#volcano)"/>
      <polygon points="300,30 200,180 400,180" fill="#3a1505" opacity="0.4"/>

      <!-- Lava glow at peak -->
      <ellipse cx="300" cy="50" rx="30" ry="15" fill="#ff4400" opacity="0.3"/>
      <ellipse cx="300" cy="50" rx="18" ry="8" fill="#ff6622" opacity="0.4"/>
      <ellipse cx="300" cy="48" rx="8" ry="4" fill="#ffaa44" opacity="0.5"/>

      <!-- Gate entrance carved into mountain -->
      <rect x="250" y="160" width="100" height="120" fill="#1a0800" stroke="#8a4400" stroke-width="2" rx="4"/>
      <!-- Archway -->
      <path d="M250,200 Q300,140 350,200" fill="#1a0800" stroke="#8a4400" stroke-width="2"/>
      <!-- Gate doors -->
      <line x1="300" y1="160" x2="300" y2="280" stroke="#6a3300" stroke-width="1"/>
      <!-- Door details -->
      <circle cx="290" cy="220" r="3" fill="#ff4400" opacity="0.5"/>
      <circle cx="310" cy="220" r="3" fill="#ff4400" opacity="0.5"/>
      <!-- Rune carvings -->
      ${[{x:260,y:175},{x:270,y:190},{x:280,y:205},{x:320,y:205},{x:330,y:190},{x:340,y:175}].map((r) => 
        `<rect x="${r.x}" y="${r.y}" width="6" height="6" fill="#ff4400" opacity="0.3" rx="1"/>`
      ).join('\n      ')}

      <!-- Steam from gate crack -->
      <path d="M298,165 Q295,140 300,120 Q305,100 298,80" stroke="#4a2a10" stroke-width="4" fill="none" opacity="0.3"/>
      <path d="M302,165 Q308,135 305,110 Q300,90 308,70" stroke="#4a2a10" stroke-width="3" fill="none" opacity="0.2"/>

      <!-- Lava flows on sides -->
      <path d="M200,200 Q190,240 185,280 Q183,300 180,340" stroke="#ff4400" stroke-width="3" fill="none" opacity="0.4"/>
      <path d="M400,195 Q412,240 418,280 Q420,310 425,340" stroke="#ff4400" stroke-width="3" fill="none" opacity="0.4"/>

      <!-- Dwarven column silhouettes at entrance -->
      <rect x="242" y="170" width="8" height="110" fill="#2a1000" opacity="0.7"/>
      <rect x="350" y="170" width="8" height="110" fill="#2a1000" opacity="0.7"/>

      <!-- Sparks/embers -->
      ${Array.from({length: 18}, (_, i) => {
        const x = 260 + (i * 7) % 80;
        const y = 50 + (i * 11) % 120;
        return `<circle cx="${x}" cy="${y}" r="${1 + i%2}" fill="#ff${(6+i%4).toString(16)}a00" opacity="${0.3 + (i%4)*0.1}"/>`;
      }).join('\n      ')}

      <!-- Rock debris at base -->
      ${[150,200,380,430,460].map((x, i) => 
        `<polygon points="${x},280 ${x+8},${272-i*2} ${x+16},280" fill="#2a1200" opacity="0.5"/>`
      ).join('\n      ')}

      <defs>
        <linearGradient id="volcano" x1="0.5" y1="0" x2="0.5" y2="1">
          <stop offset="0%" stop-color="#3a1a05"/>
          <stop offset="40%" stop-color="#2a1000"/>
          <stop offset="100%" stop-color="#1a0800"/>
        </linearGradient>
      </defs>
    `,
  },
];

test.describe('Campaign Thumbnail Generation', () => {
  for (const campaign of CAMPAIGNS) {
    test(`Generate: ${campaign.title}`, async ({ browser }) => {
      const ctx = await browser.newContext({ viewport: { width: 600, height: 340 } });
      const page = await ctx.newPage();

      const svg = `
        <svg xmlns="http://www.w3.org/2000/svg" width="600" height="340" viewBox="0 0 600 340">
          <!-- Background gradient -->
          <defs>
            <linearGradient id="bg" x1="0" y1="0" x2="0.3" y2="1">
              <stop offset="0%" stop-color="${campaign.palette.bg1}"/>
              <stop offset="100%" stop-color="${campaign.palette.bg2}"/>
            </linearGradient>
            <radialGradient id="glow" cx="0.5" cy="0.6" r="0.5">
              <stop offset="0%" stop-color="${campaign.palette.glow}" stop-opacity="0.15"/>
              <stop offset="100%" stop-color="${campaign.palette.bg1}" stop-opacity="0"/>
            </radialGradient>
            <linearGradient id="titleFade" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stop-color="${campaign.palette.bg1}" stop-opacity="0"/>
              <stop offset="60%" stop-color="${campaign.palette.bg1}" stop-opacity="0.85"/>
              <stop offset="100%" stop-color="${campaign.palette.bg1}" stop-opacity="0.95"/>
            </linearGradient>
          </defs>

          <rect width="600" height="340" fill="url(#bg)"/>
          <rect width="600" height="340" fill="url(#glow)"/>

          <!-- Vignette -->
          <rect width="600" height="340" fill="url(#titleFade)" y="200" height="140"/>

          <!-- Scene art -->
          ${campaign.scene}

          <!-- Title bar at bottom -->
          <rect x="0" y="270" width="600" height="70" fill="${campaign.palette.bg1}" opacity="0.8"/>
          <line x1="30" y1="275" x2="570" y2="275" stroke="${campaign.palette.accent}" stroke-width="1" opacity="0.5"/>
          <text x="300" y="310" text-anchor="middle" font-family="Georgia, 'Times New Roman', serif" font-size="22" font-weight="bold" fill="${campaign.palette.text}" letter-spacing="2">${campaign.title.toUpperCase()}</text>

          <!-- Subtle border -->
          <rect x="0" y="0" width="600" height="340" fill="none" stroke="${campaign.palette.accent}" stroke-width="1" opacity="0.3"/>
        </svg>
      `;

      await page.setContent(`
        <html>
          <head><style>* { margin: 0; padding: 0; } body { width: 600px; height: 340px; overflow: hidden; }</style></head>
          <body>${svg}</body>
        </html>
      `);

      await page.screenshot({
        path: `../../public/campaigns/${campaign.id}.png`,
        clip: { x: 0, y: 0, width: 600, height: 340 },
      });
      await ctx.close();
    });
  }
});
