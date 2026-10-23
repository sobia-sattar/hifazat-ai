export default function CyberLogo({ className = "w-9 h-9", size = 36 }: { className?: string; size?: number }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 48 48"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={`shrink-0 drop-shadow-[0_0_12px_rgba(56,189,248,0.45)] ${className}`}
      aria-label="HIFAZAT AI Cybersecurity Shield"
    >
      <defs>
        <linearGradient id="hifazat-shield-bg" x1="0" y1="0" x2="48" y2="48" gradientUnits="userSpaceOnUse">
          <stop stopColor="#0b2347" />
          <stop offset="0.55" stopColor="#05172e" />
          <stop offset="1" stopColor="#020a17" />
        </linearGradient>
        <linearGradient id="hifazat-border-neon" x1="8" y1="4" x2="40" y2="44" gradientUnits="userSpaceOnUse">
          <stop stopColor="#38bdf8" />
          <stop offset="0.45" stopColor="#60a5fa" />
          <stop offset="1" stopColor="#06b6d4" />
        </linearGradient>
        <linearGradient id="hifazat-h-core" x1="16" y1="14" x2="32" y2="34" gradientUnits="userSpaceOnUse">
          <stop stopColor="#f0f9ff" />
          <stop offset="0.5" stopColor="#bae6fd" />
          <stop offset="1" stopColor="#38bdf8" />
        </linearGradient>
        <filter id="hifazat-diamond-glow" x="-30%" y="-30%" width="160%" height="160%">
          <feGaussianBlur stdDeviation="1.5" result="blur" />
          <feComposite in="SourceGraphic" in2="blur" operator="over" />
        </filter>
      </defs>

      {/* Outer Hexagonal Cybersecurity Shield */}
      <path
        d="M24 3.5 L41 9.5 V23.5 C41 34.5 33 41.5 24 45 C15 41.5 7 34.5 7 23.5 V9.5 L24 3.5 Z"
        fill="url(#hifazat-shield-bg)"
        stroke="url(#hifazat-border-neon)"
        strokeWidth="2.2"
        strokeLinejoin="round"
      />

      {/* Inner Tech Radar Grid lines */}
      <path
        d="M24 8 L36 12.8 V22.5 C36 30.5 30 36.2 24 39.5 C18 36.2 12 30.5 12 22.5 V12.8 L24 8 Z"
        fill="none"
        stroke="#38bdf8"
        strokeWidth="0.8"
        strokeDasharray="2.5 2.5"
        opacity="0.45"
      />

      {/* Cyber Circuit Nodes */}
      <circle cx="24" cy="3.5" r="1.8" fill="#38bdf8" />
      <circle cx="7" cy="23.5" r="1.4" fill="#38bdf8" opacity="0.85" />
      <circle cx="41" cy="23.5" r="1.4" fill="#38bdf8" opacity="0.85" />

      {/* High-tech Stylized 'H' Emblem */}
      {/* Left Pillar */}
      <path d="M17.5 16 V32" stroke="url(#hifazat-h-core)" strokeWidth="3.2" strokeLinecap="round" />
      {/* Right Pillar */}
      <path d="M30.5 16 V32" stroke="url(#hifazat-h-core)" strokeWidth="3.2" strokeLinecap="round" />
      {/* Crossbar */}
      <path d="M17.5 24 H30.5" stroke="url(#hifazat-h-core)" strokeWidth="2.6" strokeLinecap="round" />

      {/* Central Glowing Security Core Diamond */}
      <path
        d="M24 20.8 L27.2 24 L24 27.2 L20.8 24 Z"
        fill="#ffffff"
        filter="url(#hifazat-diamond-glow)"
      />
      <circle cx="24" cy="24" r="1.1" fill="#0284c7" />
    </svg>
  );
}
