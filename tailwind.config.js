/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [],
  theme: {
    extend: {},
  },
  plugins: [],
}

module.exports = {
  content: [
    './templates/**/*.html', // Add the path to your Django templates
    './static/**/*.js',     // Add the path to your static JS files
  ],
  theme: {
    extend: {},
  },
  plugins: [require('daisyui')],
};
