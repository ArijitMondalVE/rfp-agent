/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.html",
    "./src/**/*.ts",
    "./src/**/*.{html,ts}",
  ],
  theme: {
    extend: {
      boxShadow: {
        soft: "0 10px 30px rgba(0,0,0,0.12)",
      },
      backgroundImage: {
        radial:
          "radial-gradient(circle at top left, rgba(56,189,248,0.35), rgba(99,102,241,0.18) 45%, transparent 70%)",
      },
    },
  },
  plugins: [],
};

