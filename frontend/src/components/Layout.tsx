import { useState, useEffect, useRef } from "react";
import { NavLink, Outlet, useLocation } from "react-router-dom";
import FloatingAssistant from "./FloatingAssistant";
import CyberLogo from "./CyberLogo";

const links = [
  { to: "/overview", label: "Overview", icon: "⌂" },
  { to: "/youtube", label: "YouTube", icon: "▷" },
  { to: "/analyzer", label: "Text analysis", icon: "🛡" },
  { to: "/moderation", label: "Review center", icon: "⚖" },
  { to: "/incidents", label: "Incidents", icon: "🚨" },
  { to: "/scam-check", label: "Scam check", icon: "🔍" },
  { to: "/password-check", label: "Password check", icon: "🔑" },
  { to: "/live", label: "Live monitor", icon: "📡" },
];

export default function Layout() {
  const location = useLocation();
  const [motion, setMotion] = useState(() => localStorage.getItem("hifazat-motion") !== "off");
  
  // Theme state: dark (default) | light
  const [theme, setTheme] = useState<"dark" | "light">(() => {
    const saved = localStorage.getItem("hifazat-theme");
    return saved === "light" || saved === "dark" ? saved : "dark";
  });

  // Mobile navigation dropdown state
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Sync theme with DOM and localStorage
  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
    document.body.setAttribute("data-theme", theme);
    localStorage.setItem("hifazat-theme", theme);
  }, [theme]);

  function toggleTheme() {
    setTheme((t) => (t === "dark" ? "light" : "dark"));
  }

  function toggleMotion() {
    setMotion((v) => {
      localStorage.setItem("hifazat-motion", v ? "off" : "on");
      return !v;
    });
  }

  // Close dropdown whenever the route changes
  useEffect(() => {
    setMobileMenuOpen(false);
  }, [location.pathname]);

  // Close dropdown on click outside or escape key
  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setMobileMenuOpen(false);
      }
    }
    function handleKeyDown(e: KeyboardEvent) {
      if (e.key === "Escape") setMobileMenuOpen(false);
    }
    if (mobileMenuOpen) {
      document.addEventListener("mousedown", handleClickOutside);
      document.addEventListener("keydown", handleKeyDown);
    }
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
      document.removeEventListener("keydown", handleKeyDown);
    };
  }, [mobileMenuOpen]);

  // Current active page label for mobile dropdown button
  const currentLink = links.find((l) => l.to === location.pathname);
  const activeLabel = currentLink ? currentLink.label : "Menu";

  return (
    <div className="app-shell" data-theme={theme} data-motion={motion ? "on" : "off"}>
      <div className="ambient-scene" aria-hidden="true">
        <div className="ambient-cloud cloud-a" />
        <div className="ambient-cloud cloud-b" />
        <div className="ambient-grid" />
        {Array.from({ length: 8 }, (_, i) => (
          <i className={"ambient-spark spark-" + i} key={i} />
        ))}
      </div>

      <header className="topbar">
        {/* Brand Logo & Title — Guaranteed on ONE line */}
        <NavLink to="/overview" className="brand flex items-center gap-2.5 group shrink-0 whitespace-nowrap">
          <CyberLogo size={32} className="group-hover:scale-105 transition-transform shrink-0" />
          <div className="flex items-center gap-2 whitespace-nowrap">
            <span className="brand-logo-text whitespace-nowrap font-extrabold tracking-tight text-white flex items-center gap-1.5 text-lg">
              HIFAZAT <span className="text-sky-400 font-bold">AI</span>
            </span>
            <span
              className="urdu-badge text-[11px] font-medium px-2 py-0.5 rounded-full border border-sky-400/25 bg-sky-500/10 text-sky-300 whitespace-nowrap hidden sm:inline-block"
              dir="rtl"
            >
              حفاظت
            </span>
          </div>
        </NavLink>

        {/* Desktop Navigation Links */}
        <nav aria-label="Main navigation" className="desktop-nav">
          {links.map(({ to, label }) => (
            <NavLink key={to} to={to}>
              {label}
            </NavLink>
          ))}
        </nav>

        {/* Action Controls: Theme Switcher, Settings, and Mobile Menu Toggle */}
        <div className="topbar-actions flex items-center gap-2 shrink-0">
          {/* Light / Dark Theme Button */}
          <button
            type="button"
            className="theme-toggle-btn"
            onClick={toggleTheme}
            title={theme === "dark" ? "Switch to Light theme" : "Switch to Dark theme"}
            aria-label="Toggle light or dark theme"
          >
            <span aria-hidden="true">{theme === "dark" ? "☀️" : "🌙"}</span>
            <span className="theme-text hidden sm:inline">
              {theme === "dark" ? "Light" : "Dark"}
            </span>
          </button>

          {/* Settings Link */}
          <NavLink
            to="/settings"
            className={({ isActive }) => `settings-nav-btn hidden sm:inline-flex ${isActive ? "active" : ""}`}
            title="System Settings & API Configuration"
          >
            <span aria-hidden="true">⚙️</span>
            <span>Settings</span>
          </NavLink>

          {/* Mobile Dropdown Trigger Button */}
          <div className="mobile-nav-wrapper relative" ref={dropdownRef}>
            <button
              type="button"
              className={`mobile-menu-btn ${mobileMenuOpen ? "active" : ""}`}
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              aria-expanded={mobileMenuOpen}
              aria-label="Toggle navigation menu dropdown"
            >
              <span className="menu-icon" aria-hidden="true">
                {mobileMenuOpen ? "✕" : "☰"}
              </span>
              <span className="current-page-label">{activeLabel}</span>
              <span className="dropdown-chevron" aria-hidden="true">
                ▾
              </span>
            </button>

            {/* Mobile Dropdown Panel */}
            {mobileMenuOpen && (
              <div className="mobile-dropdown-menu" role="menu">
                <div className="mobile-dropdown-header">
                  <span className="text-[10px] font-mono tracking-widest uppercase opacity-70">
                    Navigation Menu
                  </span>
                  <span className="text-xs text-sky-400 font-mono">
                    {theme === "dark" ? "Dark Mode" : "Light Mode"}
                  </span>
                </div>

                <div className="mobile-dropdown-links">
                  {links.map(({ to, label, icon }) => (
                    <NavLink
                      key={to}
                      to={to}
                      className={({ isActive }) =>
                        `mobile-nav-item ${isActive ? "active" : ""}`
                      }
                      role="menuitem"
                    >
                      <span className="mobile-nav-icon" aria-hidden="true">
                        {icon}
                      </span>
                      <span className="mobile-nav-label">{label}</span>
                      {location.pathname === to && (
                        <span className="active-dot" aria-hidden="true">
                          ●
                        </span>
                      )}
                    </NavLink>
                  ))}
                  
                  {/* Settings in Mobile Dropdown */}
                  <NavLink
                    to="/settings"
                    className={({ isActive }) =>
                      `mobile-nav-item ${isActive ? "active" : ""}`
                    }
                    role="menuitem"
                  >
                    <span className="mobile-nav-icon" aria-hidden="true">⚙️</span>
                    <span className="mobile-nav-label">Settings & API</span>
                  </NavLink>
                </div>

                <div className="mobile-dropdown-footer">
                  <button
                    type="button"
                    className="mobile-theme-btn"
                    onClick={toggleTheme}
                  >
                    <span>{theme === "dark" ? "☀️ Switch to Light Theme" : "🌙 Switch to Dark Theme"}</span>
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </header>

      <main className="workspace">
        <Outlet />
      </main>

      <footer className="site-footer">
        <div>
          <span>HIFAZAT AI (حفاظت AI) · YOUR DIGITAL WORLD, YOUR PROTECTION</span>
          <span className="hidden sm:inline">CYBER SAFETY &amp; THREAT INTELLIGENCE</span>
        </div>
        <div>
          <button type="button" className="text-button" onClick={toggleTheme}>
            Theme: {theme === "dark" ? "Dark 🌙" : "Light ☀️"}
          </button>
          <button type="button" className="text-button" onClick={toggleMotion}>
            Animation: {motion ? "on" : "off"}
          </button>
          <NavLink to="/research" className="text-button">
            Model verification &amp; metrics ↗
          </NavLink>
        </div>
      </footer>

      <FloatingAssistant />
    </div>
  );
}
