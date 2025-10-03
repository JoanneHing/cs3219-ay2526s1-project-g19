/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",        // Vite root HTML
    "./src/**/*.{js,ts,jsx,tsx}" // All React components
  ],
  theme: {
    extend: {
      colors: {
        'primary': '#026FD7',
        'primary-light': '#6495ED',
        'primary-dark': '#004A9F',
      },
      fontFamily: {
        'ubuntu': ['Ubuntu', 'sans-serif'],
      },
    },
  },
  plugins: [],
};
