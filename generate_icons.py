# -*- coding: utf-8 -*-
import os
import subprocess
import zlib
import struct

svg_content = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" width="512" height="512">
  <defs>
    <!-- Background Gradient -->
    <linearGradient id="bgGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#3730a3" />
      <stop offset="50%" stop-color="#4f46e5" />
      <stop offset="100%" stop-color="#7c3aed" />
    </linearGradient>

    <!-- Glass Glow -->
    <radialGradient id="topGlow" cx="25%" cy="15%" r="60%">
      <stop offset="0%" stop-color="#ffffff" stop-opacity="0.3" />
      <stop offset="100%" stop-color="#ffffff" stop-opacity="0" />
    </radialGradient>

    <!-- Front Card Gradient -->
    <linearGradient id="frontCardGrad" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#ffffff" />
      <stop offset="100%" stop-color="#f8fafc" />
    </linearGradient>

    <!-- Star / Gold Accent Gradient -->
    <linearGradient id="goldGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#fef08a" />
      <stop offset="50%" stop-color="#f59e0b" />
      <stop offset="100%" stop-color="#d97706" />
    </linearGradient>

    <!-- Drop Shadow Filter -->
    <filter id="cardShadow" x="-20%" y="-20%" width="140%" height="150%">
      <feDropShadow dx="0" dy="16" stdDeviation="16" flood-color="#0f172a" flood-opacity="0.35" />
    </filter>
    <filter id="glowShadow" x="-30%" y="-30%" width="160%" height="160%">
      <feDropShadow dx="0" dy="4" stdDeviation="8" flood-color="#fbbf24" flood-opacity="0.6" />
    </filter>
  </defs>

  <!-- App Squircle Base -->
  <rect width="512" height="512" rx="115" fill="url(#bgGrad)" />
  <!-- Glass Sheen Overlay -->
  <rect width="512" height="512" rx="115" fill="url(#topGlow)" />

  <!-- Tilted Background Card (Review Queue effect) -->
  <rect x="126" y="96" width="260" height="310" rx="32" 
        transform="rotate(-9 256 256)" 
        fill="#ffffff" fill-opacity="0.22" 
        stroke="#ffffff" stroke-opacity="0.4" stroke-width="3" />

  <!-- Second Slightly Tilted Card -->
  <rect x="136" y="106" width="250" height="300" rx="30" 
        transform="rotate(6 256 256)" 
        fill="#ffffff" fill-opacity="0.18" 
        stroke="#ffffff" stroke-opacity="0.3" stroke-width="2" />

  <!-- Main Front Active Flashcard -->
  <g filter="url(#cardShadow)">
    <rect x="126" y="116" width="260" height="310" rx="28" fill="url(#frontCardGrad)" stroke="#e2e8f0" stroke-width="1.5" />

    <!-- Top Badge Pill -->
    <rect x="156" y="142" width="76" height="24" rx="12" fill="#eef2ff" />
    <text x="194" y="158" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" 
          font-size="12" font-weight="700" fill="#4f46e5" text-anchor="middle">真题精读</text>

    <!-- Star Highlight Badge (GEMINI.md rule: ★ 核心考点) -->
    <g filter="url(#glowShadow)">
      <circle cx="346" cy="154" r="16" fill="url(#goldGrad)" />
      <polygon points="346,144 349,151 356,152 351,157 353,164 346,160 339,164 341,157 336,152 343,151" fill="#ffffff" />
    </g>

    <!-- Central Letter "E" and "N" or Stylized Typography -->
    <text x="256" y="275" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" 
          font-size="92" font-weight="900" fill="#312e81" text-anchor="middle" letter-spacing="-3">EN</text>

    <!-- Flashcard Divider Line -->
    <line x1="166" y1="312" x2="346" y2="312" stroke="#e0e7ff" stroke-width="2.5" stroke-linecap="round" />

    <!-- Mock Note Highlights (Core meaning & context) -->
    <rect x="176" y="332" width="160" height="12" rx="6" fill="#4f46e5" fill-opacity="0.85" />
    <rect x="196" y="354" width="120" height="10" rx="5" fill="#94a3b8" fill-opacity="0.6" />
    <rect x="221" y="372" width="70" height="8" rx="4" fill="#cbd5e1" fill-opacity="0.7" />

    <!-- Mini Bottom Indicator Dots -->
    <circle cx="236" cy="404" r="3.5" fill="#4f46e5" />
    <circle cx="256" cy="404" r="3.5" fill="#cbd5e1" />
    <circle cx="276" cy="404" r="3.5" fill="#cbd5e1" />
  </g>
</svg>
"""

with open("icons/icon.svg", "w", encoding="utf-8") as f:
    f.write(svg_content)

with open("favicon.svg", "w", encoding="utf-8") as f:
    f.write(svg_content)

print("Saved icons/icon.svg and favicon.svg")
