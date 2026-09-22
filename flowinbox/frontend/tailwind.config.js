/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          50: '#eef7ff',
          100: '#e2f0ff',
          200: '#cce5fb',
          300: '#99cbf7',
          400: '#61a8ef',
          500: '#3186d8',
          600: '#2366a8',
          700: '#1d5188',
          800: '#1b4470',
          900: '#1b3a5d',
        },
        surface: {
          page: '#EDF4FB',
          card: '#FFFFFF',
          sidebar: '#EDF4FB',
          hover: '#E4EEF8',
          active: '#DCECFB',
        },
        ink: {
          primary: '#172033',
          secondary: '#536176',
          muted: '#8995A7',
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
      },
      boxShadow: {
        'subtle': '0 1px 3px rgba(23, 32, 51, 0.05), 0 1px 2px rgba(23, 32, 51, 0.03)',
        'card': '0 4px 16px rgba(23, 32, 51, 0.04), 0 1px 2px rgba(23, 32, 51, 0.02)',
        'modal': '0 20px 40px -15px rgba(23, 32, 51, 0.12), 0 0 0 1px rgba(220, 229, 239, 0.8)',
      },
      borderRadius: {
        '2xl': '1rem',
        '3xl': '1.5rem',
      }
    },
  },
  plugins: [],
}
