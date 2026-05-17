import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        "ibm-blue": "#0f62fe",
        "ibm-blue-dark": "#0043ce",
        "ibm-red": "#da1e28",
        "ibm-green": "#24a148",
        "ibm-yellow": "#f1c21b",
        "ibm-gray": "#525252",
      },
      fontFamily: {
        sans: ["IBM Plex Sans", "system-ui", "sans-serif"],
      },
    },
  },
  plugins: [],
};

export default config;

// Made with Bob
