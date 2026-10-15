/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        background: '#0B0D12',
        surface: '#11151D',
        'surface-elevated': '#191E29',
        'border-subtle': 'rgba(148, 163, 184, 0.16)',
        'border-glow': 'rgba(167, 139, 250, 0.28)',
        primary: {
          light: '#C4B5FD',
          DEFAULT: '#9A83ED',
          deep: '#7056CC',
        },
        accent: {
          pink: '#F472B6',
          cyan: '#38BDF8',
          emerald: '#34D399',
        },
        text: {
          DEFAULT: '#EEF0F6',
          muted: '#9AA2B2',
          faint: '#697386',
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
        'violet-glow': '0 0 25px rgba(124, 58, 237, 0.18)',
        'pink-glow': '0 0 25px rgba(244, 114, 182, 0.25)',
        'subtle-panel': '0 12px 36px rgba(0, 0, 0, 0.4)',
      },
    },
  },
  plugins: [],
}
