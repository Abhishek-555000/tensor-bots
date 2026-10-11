/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        background: '#07040F',
        surface: '#120A24',
        'surface-elevated': '#1A0F33',
        'border-subtle': 'rgba(167, 139, 250, 0.18)',
        'border-glow': 'rgba(167, 139, 250, 0.35)',
        primary: {
          light: '#C4B5FD',
          DEFAULT: '#A78BFA',
          deep: '#7C3AED',
        },
        accent: {
          pink: '#F472B6',
          cyan: '#38BDF8',
          emerald: '#34D399',
        },
        text: {
          DEFAULT: '#E4E0F0',
          muted: '#8B84A3',
          faint: '#5C5474',
        },
        error: '#F87171',
      },
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'monospace'],
      },
      borderRadius: {
        'card': '16px',
        'pill': '9999px',
      },
      boxShadow: {
        'violet-glow': '0 0 25px rgba(124, 58, 237, 0.25)',
        'pink-glow': '0 0 25px rgba(244, 114, 182, 0.25)',
        'subtle-panel': '0 12px 36px rgba(0, 0, 0, 0.65)',
      },
    },
  },
  plugins: [],
}
