/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        success: "#16a34a",
        danger: "#dc2626",
        warning: "#ca8a04",
      },
    },
  },
  plugins: [],
};
