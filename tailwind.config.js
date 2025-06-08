/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./templates/*.html",
    "./static/**/*.js",
  ],
  theme: {
    extend: {
      colors: {
        'primary': '#ff4b2b',
        'secondary': '#ff416c',
      },
      animation: {
        'slide-in': 'slideIn 0.5s ease-out',
      },
      keyframes: {
        slideIn: {
          '0%': { transform: 'translateX(100%)', opacity: '0' },
          '100%': { transform: 'translateX(0)', opacity: '1' },
        }
      }
    },
  },
  plugins: [],
}