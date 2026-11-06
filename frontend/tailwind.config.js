/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        pyra: {
          bg: '#0f1117',
          surface: '#161a23',
          card: '#1c2030',
          border: '#2a2e3e',
          hover: '#252a3a',
          text: '#e1e4eb',
          muted: '#8b92a5',
          accent: '#3b82f6',
          green: '#22c55e',
          ember: '#f97316',
          danger: '#ef4444',
          warning: '#eab308',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
      },
    },
  },
  plugins: [],
}
