import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: "class",
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        "ibm-blue": { DEFAULT: "#0f62fe", dark: "#0043ce", light: "#4589ff" },
        "ibm-red": { DEFAULT: "#da1e28", dark: "#a2191f" },
        "ibm-green": { DEFAULT: "#24a148", dark: "#0e6027" },
        "ibm-yellow": { DEFAULT: "#f1c21b", dark: "#8e6a00" },
        "ibm-gray": { DEFAULT: "#525252", dark: "#262626", light: "#a8a8a8" },
        "ibm-purple": { DEFAULT: "#8a3ffc", dark: "#491d8b" },
      },
      fontFamily: {
        sans: ["IBM Plex Sans", "system-ui", "sans-serif"],
        mono: ["IBM Plex Mono", "monospace"],
      },
    },
  },
  plugins: [],
};

export default config;

// Made with Bob
