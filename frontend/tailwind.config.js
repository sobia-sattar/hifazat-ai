/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: ["Sora", "Segoe UI", "sans-serif"],
      },
      colors: {
        ink: "#07090f",
        panel: "#101522",
        line: "#1e2a3d",
      },
    },
  },
  plugins: [],
};
