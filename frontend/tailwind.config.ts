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
        term: {
          bg: "#08090B",
          panel: "#0E1013",
          raised: "#12151A",
          line: "#23272E",
          "line-bright": "#343A44",
          text: "#D7DBE0",
          muted: "#8A929E",
          faint: "#525A66",
          green: "#6EE7A8",
          "green-dim": "#3E8F68",
          amber: "#F5B84B",
          red: "#F2686B",
          blue: "#6FA8FF",
        },
      },
      fontFamily: {
        mono: ["var(--font-plex-mono)", "ui-monospace", "SFMono-Regular", "Menlo", "monospace"],
        sans: ["var(--font-inter)", "system-ui", "sans-serif"],
      },
      borderRadius: {
        none: "0",
        sm: "1px",
        DEFAULT: "2px",
        md: "2px",
        lg: "3px",
      },
      boxShadow: {
        term: "0 1px 0 rgba(255,255,255,0.03) inset, 0 12px 30px -24px rgba(0,0,0,0.9)",
      },
      keyframes: {
        "fade-up": {
          "0%": { opacity: "0", transform: "translateY(4px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        blink: {
          "0%, 49%": { opacity: "1" },
          "50%, 100%": { opacity: "0" },
        },
      },
      animation: {
        "fade-up": "fade-up 300ms ease-out both",
        blink: "blink 1.1s step-end infinite",
      },
    },
  },
  plugins: [],
};

export default config;
