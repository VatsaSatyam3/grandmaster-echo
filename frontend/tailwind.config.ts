import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          DEFAULT: "#4F46E5",
          50: "#EEEDFC",
          100: "#DDDAFA",
          200: "#BAB5F5",
          300: "#9890EF",
          400: "#756BEA",
          500: "#4F46E5",
          600: "#2A20CB",
          700: "#20189A",
          800: "#161069",
          900: "#0C0838",
        },
        accent: {
          DEFAULT: "#F59E0B",
          50: "#FEF3C7",
          100: "#FDE68A",
          200: "#FCD34D",
          300: "#FBBF24",
          400: "#F59E0B",
          500: "#D97706",
          600: "#B45309",
          700: "#92400E",
          800: "#78350F",
          900: "#451A03",
        },
        surface: {
          DEFAULT: "#0F172A",
          light: "#1E293B",
        },
        card: {
          DEFAULT: "#1E293B",
          hover: "#334155",
        },
      },
      animation: {
        "glow-pulse": "glow-pulse 3s ease-in-out infinite",
        "fade-in": "fade-in 0.5s ease-out",
        "slide-up": "slide-up 0.5s ease-out",
        "spin-slow": "spin 3s linear infinite",
      },
      keyframes: {
        "glow-pulse": {
          "0%, 100%": {
            boxShadow: "0 0 15px rgba(79, 70, 229, 0.3)",
          },
          "50%": {
            boxShadow: "0 0 30px rgba(79, 70, 229, 0.6)",
          },
        },
        "fade-in": {
          "0%": { opacity: "0" },
          "100%": { opacity: "1" },
        },
        "slide-up": {
          "0%": { opacity: "0", transform: "translateY(20px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
      },
    },
  },
  plugins: [],
};

export default config;
