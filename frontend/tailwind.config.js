/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      fontFamily: {
        display: ['"Space Mono"', 'ui-monospace', 'monospace'],
        body: ['"IBM Plex Sans"', 'system-ui', 'sans-serif'],
      },
      colors: {
        ink: '#0a0e14',
        panel: '#11161d',
        edge: '#1d242e',
        accent: '#7CFFB2',  // signal-green
        warn: '#FFB454',
      },
    },
  },
  plugins: [],
}
