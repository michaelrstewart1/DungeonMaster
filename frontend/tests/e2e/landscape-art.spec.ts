/**
 * Generate epic fantasy landscape art for the home page background slideshow.
 * Wide format (1920x1080) with atmospheric dark fantasy scenes.
 * Each scene is a layered SVG with mountains, structures, skies, and effects.
 */
import { test } from '@playwright/test';

interface Landscape {
  id: string;
  name: string;
  svg: string;
}

const W = 1920;
const H = 1080;

const LANDSCAPES: Landscape[] = [
  {
    id: 'dragon-peak',
    name: 'Dragon Peak',
    svg: `<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}">
      <defs>
        <linearGradient id="sky1" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stop-color="#0a0512"/>
          <stop offset="40%" stop-color="#1a0a2a"/>
          <stop offset="100%" stop-color="#2a1535"/>
        </linearGradient>
        <radialGradient id="moon1" cx="0.5" cy="0.5" r="0.5">
          <stop offset="0%" stop-color="#fff8e0" stop-opacity="0.9"/>
          <stop offset="60%" stop-color="#ddc870" stop-opacity="0.3"/>
          <stop offset="100%" stop-color="#ddc870" stop-opacity="0"/>
        </radialGradient>
        <filter id="glow1" x="-50%" y="-50%" width="200%" height="200%">
          <feGaussianBlur stdDeviation="20" result="blur"/>
          <feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>
        </filter>
      </defs>

      <!-- Sky -->
      <rect width="${W}" height="${H}" fill="url(#sky1)"/>

      <!-- Stars -->
      ${Array.from({length: 80}, (_, i) => {
        const x = Math.sin(i * 137.508) * 900 + 960;
        const y = Math.cos(i * 97.3) * 300 + 250;
        const r = (i % 3 === 0) ? 1.5 : 0.8;
        const o = 0.3 + (i % 5) * 0.12;
        return `<circle cx="${x}" cy="${y}" r="${r}" fill="#fff" opacity="${o}"/>`;
      }).join('\n      ')}

      <!-- Moon -->
      <circle cx="1500" cy="180" r="60" fill="url(#moon1)" filter="url(#glow1)"/>
      <circle cx="1520" cy="170" r="55" fill="#0a0512" opacity="0.6"/>

      <!-- Far mountains (purple haze) -->
      <path d="M0,700 L200,450 L400,550 L600,380 L800,500 L1000,350 L1200,480 L1400,400 L1600,520 L1800,430 L1920,500 L1920,1080 L0,1080Z" fill="#1a0f28" opacity="0.7"/>

      <!-- Mid mountains -->
      <path d="M0,750 L150,550 L350,650 L550,480 L750,600 L950,450 L1100,580 L1300,470 L1500,560 L1700,500 L1920,600 L1920,1080 L0,1080Z" fill="#150c22" opacity="0.85"/>

      <!-- Dragon silhouette on peak -->
      <g transform="translate(1050, 380)">
        <!-- Body -->
        <path d="M0,0 Q-30,-20 -50,-10 Q-80,0 -90,30 Q-95,50 -80,60 L-40,50 Q-20,55 0,50 Q30,40 40,20 Q50,5 35,-10 Q15,-15 0,0Z" fill="#0d0820" opacity="0.9"/>
        <!-- Wing left -->
        <path d="M-40,10 Q-100,-60 -160,-30 Q-130,-10 -90,0 Q-80,-20 -40,10Z" fill="#0d0820" opacity="0.85"/>
        <!-- Wing right -->
        <path d="M20,5 Q80,-70 150,-40 Q120,-15 80,-5 Q70,-25 20,5Z" fill="#0d0820" opacity="0.85"/>
        <!-- Neck/head -->
        <path d="M-50,-10 Q-65,-30 -70,-45 Q-68,-50 -60,-48 Q-55,-35 -45,-20Z" fill="#0d0820" opacity="0.9"/>
        <!-- Eye glow -->
        <circle cx="-62" cy="-44" r="2" fill="#ff4400" opacity="0.8"/>
      </g>

      <!-- Near mountains (dark) -->
      <path d="M0,800 L100,650 L250,720 L400,600 L600,700 L800,620 L1000,680 L1200,600 L1400,660 L1600,620 L1800,700 L1920,650 L1920,1080 L0,1080Z" fill="#0d0818"/>

      <!-- Foreground dark -->
      <path d="M0,900 Q200,870 500,880 Q800,890 1100,870 Q1400,860 1700,880 L1920,870 L1920,1080 L0,1080Z" fill="#080510"/>

      <!-- Mist layers -->
      <rect x="0" y="650" width="${W}" height="100" fill="#1a0f28" opacity="0.15"/>
      <rect x="0" y="750" width="${W}" height="80" fill="#1a0f28" opacity="0.1"/>

      <!-- Ember particles -->
      ${Array.from({length: 15}, (_, i) => {
        const x = 900 + Math.sin(i * 50) * 300;
        const y = 350 + Math.cos(i * 70) * 100;
        return `<circle cx="${x}" cy="${y}" r="1.2" fill="#ff6622" opacity="${0.2 + (i%4)*0.1}"/>`;
      }).join('\n      ')}
    </svg>`
  },

  {
    id: 'ancient-citadel',
    name: 'Ancient Citadel',
    svg: `<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}">
      <defs>
        <linearGradient id="sky2" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stop-color="#050510"/>
          <stop offset="50%" stop-color="#0d0a1a"/>
          <stop offset="100%" stop-color="#1a1228"/>
        </linearGradient>
        <radialGradient id="glow2" cx="0.7" cy="0.3" r="0.5">
          <stop offset="0%" stop-color="#d4a846" stop-opacity="0.08"/>
          <stop offset="100%" stop-color="#d4a846" stop-opacity="0"/>
        </radialGradient>
      </defs>

      <rect width="${W}" height="${H}" fill="url(#sky2)"/>
      <rect width="${W}" height="${H}" fill="url(#glow2)"/>

      <!-- Stars -->
      ${Array.from({length: 60}, (_, i) => {
        const x = ((i * 31.7) % 1920);
        const y = ((i * 23.1 + 50) % 500);
        const r = (i % 4 === 0) ? 1.2 : 0.6;
        return `<circle cx="${x}" cy="${y}" r="${r}" fill="#c0c0e0" opacity="${0.2 + (i%5)*0.1}"/>`;
      }).join('\n      ')}

      <!-- Aurora / nebula band -->
      <ellipse cx="1200" cy="200" rx="600" ry="120" fill="#2a1858" opacity="0.15"/>
      <ellipse cx="1100" cy="220" rx="400" ry="80" fill="#4a2080" opacity="0.08"/>

      <!-- Distant cliff walls -->
      <path d="M0,800 L0,500 L100,520 L200,400 L300,450 L400,380 L500,420 L600,350 L700,400 L800,500 L900,480 L1000,520 L1920,600 L1920,1080 L0,1080Z" fill="#0f0a1a" opacity="0.6"/>

      <!-- Citadel structure (right side) -->
      <g transform="translate(1300, 200)">
        <!-- Main tower -->
        <rect x="0" y="100" width="80" height="400" fill="#0d0918" stroke="#2a1f40" stroke-width="1"/>
        <polygon points="0,100 40,40 80,100" fill="#0d0918" stroke="#2a1f40" stroke-width="1"/>
        <!-- Spire -->
        <line x1="40" y1="40" x2="40" y2="0" stroke="#2a1f40" stroke-width="2"/>
        <circle cx="40" cy="0" r="4" fill="#d4a846" opacity="0.6"/>

        <!-- Left wing -->
        <rect x="-60" y="200" width="60" height="300" fill="#0a0714" stroke="#2a1f40" stroke-width="0.8"/>
        <polygon points="-60,200 -30,160 0,200" fill="#0a0714" stroke="#2a1f40" stroke-width="0.8"/>

        <!-- Right wing -->
        <rect x="80" y="220" width="50" height="280" fill="#0a0714" stroke="#2a1f40" stroke-width="0.8"/>
        <polygon points="80,220 105,180 130,220" fill="#0a0714" stroke="#2a1f40" stroke-width="0.8"/>

        <!-- Far right tower -->
        <rect x="160" y="180" width="40" height="320" fill="#080612" stroke="#2a1f40" stroke-width="0.6"/>
        <polygon points="160,180 180,130 200,180" fill="#080612" stroke="#2a1f40" stroke-width="0.6"/>

        <!-- Window lights -->
        <rect x="15" y="160" width="10" height="15" rx="2" fill="#d4a846" opacity="0.3"/>
        <rect x="55" y="160" width="10" height="15" rx="2" fill="#d4a846" opacity="0.2"/>
        <rect x="15" y="250" width="10" height="15" rx="2" fill="#d4a846" opacity="0.15"/>
        <rect x="55" y="300" width="10" height="15" rx="2" fill="#d4a846" opacity="0.25"/>
        <rect x="-40" y="280" width="8" height="12" rx="2" fill="#d4a846" opacity="0.2"/>
        <rect x="95" y="310" width="8" height="12" rx="2" fill="#d4a846" opacity="0.15"/>
      </g>

      <!-- Bridge / causeway -->
      <path d="M1100,650 Q1200,620 1240,620 L1300,620 Q1350,620 1400,650" fill="none" stroke="#1a1230" stroke-width="6"/>
      <path d="M1100,650 Q1200,640 1240,640 L1300,640 Q1350,640 1400,650" fill="none" stroke="#1a1230" stroke-width="3"/>

      <!-- Foreground rocks -->
      <path d="M0,850 Q100,830 250,840 Q400,800 600,830 Q800,820 1000,850 L1920,800 L1920,1080 L0,1080Z" fill="#080510"/>

      <!-- Mist -->
      <ellipse cx="1200" cy="700" rx="500" ry="40" fill="#1a1230" opacity="0.2"/>
    </svg>`
  },

  {
    id: 'enchanted-forest',
    name: 'Enchanted Forest',
    svg: `<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}">
      <defs>
        <linearGradient id="sky3" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stop-color="#060810"/>
          <stop offset="60%" stop-color="#0a1018"/>
          <stop offset="100%" stop-color="#0f1a20"/>
        </linearGradient>
        <radialGradient id="moonlight3" cx="0.8" cy="0.15" r="0.4">
          <stop offset="0%" stop-color="#88bbff" stop-opacity="0.06"/>
          <stop offset="100%" stop-color="#88bbff" stop-opacity="0"/>
        </radialGradient>
      </defs>

      <rect width="${W}" height="${H}" fill="url(#sky3)"/>
      <rect width="${W}" height="${H}" fill="url(#moonlight3)"/>

      <!-- Stars through canopy -->
      ${Array.from({length: 30}, (_, i) => {
        const x = ((i * 67.3) % 1920);
        const y = ((i * 19.7) % 300);
        return `<circle cx="${x}" cy="${y}" r="0.8" fill="#aaddff" opacity="${0.15 + (i%4)*0.08}"/>`;
      }).join('\n      ')}

      <!-- Giant trees — far layer -->
      ${[300, 700, 1100, 1500, 1800].map((x, i) => {
        const h = 500 + (i % 3) * 100;
        const w = 40 + (i % 2) * 20;
        return `
        <rect x="${x - w/2}" y="${H - h}" width="${w}" height="${h}" fill="#0a1510" opacity="0.5"/>
        <ellipse cx="${x}" cy="${H - h}" rx="${80 + i*10}" ry="${100 + i*15}" fill="#0a1a12" opacity="0.4"/>
        `;
      }).join('')}

      <!-- Giant trees — mid layer -->
      ${[100, 500, 900, 1400, 1700].map((x, i) => {
        const h = 600 + (i % 3) * 80;
        const w = 50 + (i % 2) * 25;
        return `
        <rect x="${x - w/2}" y="${H - h}" width="${w}" height="${h}" fill="#081210" opacity="0.7"/>
        <ellipse cx="${x}" cy="${H - h + 20}" rx="${100 + i*8}" ry="${120 + i*10}" fill="#0a1810" opacity="0.6"/>
        `;
      }).join('')}

      <!-- Hanging vines / roots -->
      ${[200, 650, 1050, 1550].map((x, i) => `
        <path d="M${x},${200 + i*30} Q${x + 20},${350 + i*20} ${x - 10},${500 + i*40}" fill="none" stroke="#1a3020" stroke-width="2" opacity="0.4"/>
        <path d="M${x + 50},${180 + i*25} Q${x + 40},${320 + i*15} ${x + 60},${480 + i*35}" fill="none" stroke="#1a3020" stroke-width="1.5" opacity="0.3"/>
      `).join('')}

      <!-- Magical particles (firefly-like) -->
      ${Array.from({length: 25}, (_, i) => {
        const x = 200 + (i * 71) % 1600;
        const y = 300 + (i * 43) % 500;
        const r = 2 + (i % 3);
        const colors = ['#66ff88', '#88ffaa', '#44dd66', '#aaffcc'];
        return `<circle cx="${x}" cy="${y}" r="${r}" fill="${colors[i%4]}" opacity="${0.15 + (i%5)*0.05}"/>`;
      }).join('\n      ')}

      <!-- Ground glow -->
      <ellipse cx="960" cy="${H}" rx="800" ry="80" fill="#1a4030" opacity="0.1"/>

      <!-- Foreground dark -->
      <path d="M0,900 Q300,880 600,890 Q900,870 1200,885 Q1500,875 1920,900 L1920,1080 L0,1080Z" fill="#060a08"/>

      <!-- Ground roots -->
      <path d="M0,950 Q200,930 400,940 Q500,950 600,935 Q900,940 1200,930 Q1500,945 1920,935 L1920,1080 L0,1080Z" fill="#050808"/>
    </svg>`
  },

  {
    id: 'volcanic-wasteland',
    name: 'Volcanic Wasteland',
    svg: `<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}">
      <defs>
        <linearGradient id="sky4" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stop-color="#0a0508"/>
          <stop offset="40%" stop-color="#1a0a0a"/>
          <stop offset="100%" stop-color="#2a1510"/>
        </linearGradient>
        <radialGradient id="lava-glow" cx="0.6" cy="0.7" r="0.5">
          <stop offset="0%" stop-color="#ff4400" stop-opacity="0.08"/>
          <stop offset="100%" stop-color="#ff4400" stop-opacity="0"/>
        </radialGradient>
      </defs>

      <rect width="${W}" height="${H}" fill="url(#sky4)"/>
      <rect width="${W}" height="${H}" fill="url(#lava-glow)"/>

      <!-- Ash clouds -->
      <ellipse cx="500" cy="150" rx="400" ry="80" fill="#2a1510" opacity="0.2"/>
      <ellipse cx="1300" cy="100" rx="350" ry="60" fill="#2a1510" opacity="0.15"/>
      <ellipse cx="900" cy="200" rx="500" ry="90" fill="#1a0a08" opacity="0.2"/>

      <!-- Volcano (background, right) -->
      <path d="M1200,800 L1450,300 L1500,310 L1750,800Z" fill="#1a0a08"/>
      <path d="M1430,300 L1450,260 L1470,270 L1520,310Z" fill="#2a1208" opacity="0.8"/>

      <!-- Eruption glow -->
      <ellipse cx="1475" cy="280" rx="40" ry="60" fill="#ff4400" opacity="0.1"/>
      <ellipse cx="1475" cy="280" rx="20" ry="30" fill="#ff6622" opacity="0.15"/>

      <!-- Distant volcanos -->
      <path d="M200,800 L400,450 L600,800Z" fill="#120808" opacity="0.6"/>
      <path d="M800,800 L950,500 L1100,800Z" fill="#150a08" opacity="0.5"/>

      <!-- Lava rivers -->
      <path d="M1400,700 Q1300,720 1200,750 Q1000,780 800,790 Q600,800 400,830" fill="none" stroke="#cc3300" stroke-width="3" opacity="0.25"/>
      <path d="M1400,700 Q1300,720 1200,750 Q1000,780 800,790 Q600,800 400,830" fill="none" stroke="#ff6622" stroke-width="1" opacity="0.15"/>

      <!-- Cracked ground -->
      <path d="M0,850 L1920,820 L1920,1080 L0,1080Z" fill="#100808"/>
      ${Array.from({length: 12}, (_, i) => {
        const x1 = i * 170;
        const x2 = x1 + 40 + (i%3)*30;
        return `<line x1="${x1}" y1="${860 + (i%3)*10}" x2="${x2}" y2="${870 + (i%4)*15}" stroke="#cc3300" stroke-width="1" opacity="${0.1 + (i%3)*0.05}"/>`;
      }).join('\n      ')}

      <!-- Ember particles rising -->
      ${Array.from({length: 30}, (_, i) => {
        const x = 1200 + Math.sin(i * 40) * 400;
        const y = 200 + (i * 23) % 500;
        const r = 0.8 + (i % 3) * 0.5;
        return `<circle cx="${x}" cy="${y}" r="${r}" fill="#ff6622" opacity="${0.15 + (i%5)*0.06}"/>`;
      }).join('\n      ')}

      <!-- Smoke columns -->
      <ellipse cx="1475" cy="200" rx="30" ry="80" fill="#2a1510" opacity="0.15"/>
      <ellipse cx="1460" cy="150" rx="50" ry="100" fill="#1a0a08" opacity="0.1"/>
    </svg>`
  },

  {
    id: 'frozen-throne',
    name: 'Frozen Throne',
    svg: `<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}">
      <defs>
        <linearGradient id="sky5" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stop-color="#050810"/>
          <stop offset="50%" stop-color="#0a1020"/>
          <stop offset="100%" stop-color="#101828"/>
        </linearGradient>
        <radialGradient id="aurora5" cx="0.5" cy="0.2" r="0.6">
          <stop offset="0%" stop-color="#4488cc" stop-opacity="0.06"/>
          <stop offset="50%" stop-color="#2266aa" stop-opacity="0.03"/>
          <stop offset="100%" stop-color="#2266aa" stop-opacity="0"/>
        </radialGradient>
      </defs>

      <rect width="${W}" height="${H}" fill="url(#sky5)"/>
      <rect width="${W}" height="${H}" fill="url(#aurora5)"/>

      <!-- Aurora bands -->
      <path d="M0,100 Q400,60 800,120 Q1200,80 1600,130 Q1800,100 1920,140" fill="none" stroke="#4488cc" stroke-width="30" opacity="0.04"/>
      <path d="M0,160 Q300,120 700,180 Q1100,140 1500,190 Q1700,150 1920,200" fill="none" stroke="#22aa88" stroke-width="20" opacity="0.03"/>

      <!-- Stars -->
      ${Array.from({length: 50}, (_, i) => {
        const x = ((i * 41.3) % 1920);
        const y = ((i * 17.7) % 400);
        return `<circle cx="${x}" cy="${y}" r="${(i%3===0)?1.2:0.6}" fill="#cceeff" opacity="${0.2 + (i%4)*0.1}"/>`;
      }).join('\n      ')}

      <!-- Ice mountains far -->
      <path d="M0,700 L200,400 L350,500 L500,350 L700,480 L900,380 L1100,450 L1300,370 L1500,460 L1700,400 L1920,500 L1920,1080 L0,1080Z" fill="#0a1520" opacity="0.6"/>

      <!-- Ice mountains mid -->
      <path d="M0,750 L150,500 L300,580 L500,430 L700,550 L900,460 L1100,530 L1300,450 L1500,540 L1700,480 L1920,560 L1920,1080 L0,1080Z" fill="#081218"/>

      <!-- Giant ice throne (right center) -->
      <g transform="translate(1350, 300)">
        <!-- Back crystal spires -->
        <polygon points="-80,200 -60,50 -40,200" fill="#0a1825" stroke="#3388aa" stroke-width="0.5" opacity="0.7"/>
        <polygon points="80,200 100,30 120,200" fill="#0a1825" stroke="#3388aa" stroke-width="0.5" opacity="0.7"/>

        <!-- Main throne -->
        <polygon points="-50,200 -30,80 0,60 30,80 50,200" fill="#0c1a28" stroke="#4499bb" stroke-width="0.8"/>

        <!-- Central crystal -->
        <polygon points="-10,80 0,20 10,80" fill="#1a3050" stroke="#66bbdd" stroke-width="0.5"/>

        <!-- Ice glow -->
        <ellipse cx="0" cy="100" rx="60" ry="30" fill="#4488cc" opacity="0.05"/>
      </g>

      <!-- Frozen lake -->
      <ellipse cx="960" cy="820" rx="800" ry="60" fill="#0a1520" opacity="0.3"/>
      <path d="M300,815 L500,818 L700,812 L900,820 L1100,813 L1400,818 L1600,810" fill="none" stroke="#3388aa" stroke-width="0.5" opacity="0.15"/>

      <!-- Snow ground -->
      <path d="M0,850 Q300,840 600,845 Q900,835 1200,842 Q1500,838 1920,845 L1920,1080 L0,1080Z" fill="#0a1018"/>

      <!-- Snowflake particles -->
      ${Array.from({length: 20}, (_, i) => {
        const x = (i * 97) % 1920;
        const y = 200 + (i * 53) % 600;
        return `<circle cx="${x}" cy="${y}" r="1.5" fill="#cceeff" opacity="${0.08 + (i%4)*0.04}"/>`;
      }).join('\n      ')}
    </svg>`
  },

  {
    id: 'abyssal-depths',
    name: 'Abyssal Depths',
    svg: `<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}">
      <defs>
        <linearGradient id="sky6" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stop-color="#08050f"/>
          <stop offset="50%" stop-color="#0f0820"/>
          <stop offset="100%" stop-color="#150a30"/>
        </linearGradient>
        <radialGradient id="portal6" cx="0.65" cy="0.35" r="0.25">
          <stop offset="0%" stop-color="#8844cc" stop-opacity="0.12"/>
          <stop offset="50%" stop-color="#6622aa" stop-opacity="0.05"/>
          <stop offset="100%" stop-color="#6622aa" stop-opacity="0"/>
        </radialGradient>
      </defs>

      <rect width="${W}" height="${H}" fill="url(#sky6)"/>
      <rect width="${W}" height="${H}" fill="url(#portal6)"/>

      <!-- Swirling void -->
      <ellipse cx="1250" cy="380" rx="150" ry="150" fill="none" stroke="#6622aa" stroke-width="2" opacity="0.08"/>
      <ellipse cx="1250" cy="380" rx="100" ry="100" fill="none" stroke="#8844cc" stroke-width="1.5" opacity="0.06"/>
      <ellipse cx="1250" cy="380" rx="50" ry="50" fill="#8844cc" opacity="0.04"/>

      <!-- Floating rock islands -->
      <g transform="translate(400, 500)">
        <ellipse cx="0" cy="0" rx="120" ry="30" fill="#0f0820"/>
        <path d="M-120,0 Q-100,60 -50,80 Q0,90 50,80 Q100,60 120,0" fill="#0a0618"/>
        <!-- Ruined pillars on island -->
        <rect x="-40" y="-60" width="12" height="60" fill="#1a1030" stroke="#3a2060" stroke-width="0.5"/>
        <rect x="20" y="-45" width="10" height="45" fill="#1a1030" stroke="#3a2060" stroke-width="0.5"/>
      </g>

      <g transform="translate(1000, 350)">
        <ellipse cx="0" cy="0" rx="80" ry="20" fill="#0f0820"/>
        <path d="M-80,0 Q-60,40 -30,50 Q0,55 30,50 Q60,40 80,0" fill="#0a0618"/>
      </g>

      <g transform="translate(1500, 600)">
        <ellipse cx="0" cy="0" rx="100" ry="25" fill="#0f0820"/>
        <path d="M-100,0 Q-80,50 -40,65 Q0,70 40,65 Q80,50 100,0" fill="#0a0618"/>
        <!-- Obelisk -->
        <polygon points="-8,-80 0,-100 8,-80 8,0 -8,0" fill="#1a1030" stroke="#6622aa" stroke-width="0.5"/>
        <circle cx="0" cy="-90" r="3" fill="#8844cc" opacity="0.3"/>
      </g>

      <!-- Chain links between islands -->
      <path d="M520,500 Q700,420 920,350" fill="none" stroke="#1a1030" stroke-width="2" opacity="0.2" stroke-dasharray="8,12"/>
      <path d="M1080,370 Q1250,480 1400,590" fill="none" stroke="#1a1030" stroke-width="2" opacity="0.2" stroke-dasharray="8,12"/>

      <!-- Purple energy particles -->
      ${Array.from({length: 30}, (_, i) => {
        const x = 800 + Math.sin(i * 37) * 500;
        const y = 200 + (i * 29) % 600;
        const r = 1 + (i % 3);
        return `<circle cx="${x}" cy="${y}" r="${r}" fill="#8844cc" opacity="${0.08 + (i%5)*0.04}"/>`;
      }).join('\n      ')}

      <!-- Bottom void -->
      <path d="M0,900 Q400,880 800,890 Q1200,870 1920,900 L1920,1080 L0,1080Z" fill="#05030a"/>
    </svg>`
  },

  {
    id: 'celestial-sanctum',
    name: 'Celestial Sanctum',
    svg: `<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}">
      <defs>
        <linearGradient id="sky7" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stop-color="#080a15"/>
          <stop offset="40%" stop-color="#0d1020"/>
          <stop offset="100%" stop-color="#151830"/>
        </linearGradient>
        <radialGradient id="divine7" cx="0.5" cy="0.25" r="0.4">
          <stop offset="0%" stop-color="#d4a846" stop-opacity="0.1"/>
          <stop offset="50%" stop-color="#d4a846" stop-opacity="0.03"/>
          <stop offset="100%" stop-color="#d4a846" stop-opacity="0"/>
        </radialGradient>
      </defs>

      <rect width="${W}" height="${H}" fill="url(#sky7)"/>
      <rect width="${W}" height="${H}" fill="url(#divine7)"/>

      <!-- Constellation pattern -->
      ${Array.from({length: 70}, (_, i) => {
        const x = ((i * 29.3) % 1920);
        const y = ((i * 17.1) % 500);
        const r = (i % 5 === 0) ? 1.5 : 0.7;
        return `<circle cx="${x}" cy="${y}" r="${r}" fill="#ffe8a0" opacity="${0.15 + (i%6)*0.06}"/>`;
      }).join('\n      ')}

      <!-- Cloud layer (golden-tinged) -->
      <ellipse cx="400" cy="350" rx="300" ry="50" fill="#1a1530" opacity="0.3"/>
      <ellipse cx="1200" cy="300" rx="400" ry="60" fill="#1a1530" opacity="0.25"/>
      <ellipse cx="800" cy="380" rx="250" ry="40" fill="#1a1530" opacity="0.2"/>

      <!-- Massive temple structure (center-right) -->
      <g transform="translate(1200, 350)">
        <!-- Base platform -->
        <path d="M-200,200 L-180,180 L180,180 L200,200Z" fill="#101525" stroke="#d4a846" stroke-width="0.5" opacity="0.7"/>

        <!-- Main columns -->
        ${[-120, -60, 0, 60, 120].map(x => `
          <rect x="${x - 8}" y="20" width="16" height="160" fill="#101525" stroke="#d4a846" stroke-width="0.4" opacity="0.7"/>
        `).join('')}

        <!-- Triangular pediment -->
        <polygon points="-140,20 0,-50 140,20" fill="#0d1020" stroke="#d4a846" stroke-width="0.8" opacity="0.7"/>

        <!-- Central divine light -->
        <ellipse cx="0" cy="100" rx="50" ry="80" fill="#d4a846" opacity="0.03"/>
        <line x1="0" y1="20" x2="0" y2="180" stroke="#d4a846" stroke-width="1" opacity="0.1"/>
      </g>

      <!-- Floating steps / path -->
      ${[0, 1, 2, 3, 4].map(i => `
        <rect x="${900 + i * 60}" y="${520 - i * 30}" width="50" height="8" rx="2" fill="#101525" stroke="#d4a846" stroke-width="0.3" opacity="${0.3 + i*0.05}"/>
      `).join('')}

      <!-- Light rays from above -->
      <polygon points="940,0 980,500 920,500" fill="#d4a846" opacity="0.015"/>
      <polygon points="1180,0 1220,400 1140,400" fill="#d4a846" opacity="0.02"/>
      <polygon points="1400,0 1430,350 1370,350" fill="#d4a846" opacity="0.015"/>

      <!-- Foreground clouds -->
      <ellipse cx="300" cy="850" rx="400" ry="60" fill="#0d1020" opacity="0.4"/>
      <ellipse cx="1400" cy="870" rx="500" ry="70" fill="#0d1020" opacity="0.3"/>

      <!-- Bottom -->
      <path d="M0,920 Q400,900 800,910 Q1200,895 1920,920 L1920,1080 L0,1080Z" fill="#080a12"/>
    </svg>`
  },

  {
    id: 'stormy-seas',
    name: 'Stormy Seas',
    svg: `<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}">
      <defs>
        <linearGradient id="sky8" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stop-color="#080a10"/>
          <stop offset="40%" stop-color="#101520"/>
          <stop offset="100%" stop-color="#1a2030"/>
        </linearGradient>
      </defs>

      <rect width="${W}" height="${H}" fill="url(#sky8)"/>

      <!-- Lightning flash (faint) -->
      <path d="M1300,0 L1280,200 L1310,200 L1270,400" fill="none" stroke="#aaccff" stroke-width="2" opacity="0.06"/>
      <path d="M1310,200 L1330,350" fill="none" stroke="#aaccff" stroke-width="1" opacity="0.04"/>

      <!-- Storm clouds -->
      <ellipse cx="400" cy="200" rx="500" ry="120" fill="#101520" opacity="0.5"/>
      <ellipse cx="1000" cy="150" rx="600" ry="130" fill="#0d1218" opacity="0.6"/>
      <ellipse cx="1500" cy="250" rx="450" ry="100" fill="#101520" opacity="0.4"/>

      <!-- Ghost ship silhouette (right side) -->
      <g transform="translate(1400, 450)">
        <!-- Hull -->
        <path d="M-80,30 Q-100,0 -70,-10 L70,-10 Q100,0 80,30 Q40,50 -40,50Z" fill="#0a0e15" opacity="0.8"/>
        <!-- Masts -->
        <line x1="-20" y1="-10" x2="-20" y2="-120" stroke="#1a2030" stroke-width="3"/>
        <line x1="30" y1="-10" x2="30" y2="-100" stroke="#1a2030" stroke-width="2.5"/>
        <!-- Tattered sails -->
        <path d="M-20,-110 Q10,-90 -18,-50" fill="#1a2030" opacity="0.5"/>
        <path d="M30,-90 Q55,-75 32,-45" fill="#1a2030" opacity="0.4"/>
        <!-- Ghostly glow -->
        <ellipse cx="0" cy="0" rx="80" ry="40" fill="#88aacc" opacity="0.03"/>
      </g>

      <!-- Waves — far -->
      <path d="M0,600 Q100,580 200,590 Q400,570 600,585 Q800,575 1000,590 Q1200,580 1400,595 Q1600,575 1920,600 L1920,1080 L0,1080Z" fill="#0a1218" opacity="0.7"/>

      <!-- Waves — mid -->
      <path d="M0,700 Q150,680 300,690 Q500,675 700,688 Q900,678 1100,692 Q1300,682 1500,695 Q1700,680 1920,700 L1920,1080 L0,1080Z" fill="#081015"/>

      <!-- Wave crests (foam) -->
      <path d="M100,695 Q130,690 160,695" fill="none" stroke="#4a6080" stroke-width="1" opacity="0.15"/>
      <path d="M500,682 Q540,676 580,682" fill="none" stroke="#4a6080" stroke-width="1" opacity="0.12"/>
      <path d="M900,685 Q945,678 990,685" fill="none" stroke="#4a6080" stroke-width="1" opacity="0.1"/>
      <path d="M1300,688 Q1340,682 1380,688" fill="none" stroke="#4a6080" stroke-width="1" opacity="0.13"/>

      <!-- Waves — near -->
      <path d="M0,800 Q200,780 400,790 Q600,775 800,788 Q1000,780 1200,792 Q1400,778 1600,790 Q1800,782 1920,800 L1920,1080 L0,1080Z" fill="#060c12"/>

      <!-- Deep water -->
      <rect x="0" y="880" width="${W}" height="200" fill="#050a0f"/>
    </svg>`
  },
];

for (const landscape of LANDSCAPES) {
  test(`generate landscape: ${landscape.name}`, async ({ page }) => {
    const outDir = './public/art/landscapes';
    const outPath = `${outDir}/${landscape.id}.png`;

    // Ensure directory exists
    const fs = await import('fs');
    if (!fs.existsSync(outDir)) {
      fs.mkdirSync(outDir, { recursive: true });
    }

    await page.setViewportSize({ width: W, height: H });
    await page.setContent(`
      <!DOCTYPE html>
      <html><body style="margin:0;padding:0;background:#000;overflow:hidden">
        ${landscape.svg}
      </body></html>
    `);

    await page.screenshot({
      path: outPath,
      clip: { x: 0, y: 0, width: W, height: H },
    });
  });
}
