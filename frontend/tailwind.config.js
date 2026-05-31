import defaultConfig from "tailwindcss/defaultConfig";

export default {
  content: ["./index.html", "./src/**/*.{js,jsx,ts,tsx}"],
  theme: {
    extend: {
      colors: {
        primary: "#0066ff",
        secondary: "#00d4ff",
        dark: "#0a0e27",
        darker: "#050a1a",
      },
      backgroundImage: {
        "gradient-primary": "linear-gradient(135deg, #0066ff 0%, #00d4ff 100%)",
        "gradient-dark": "linear-gradient(135deg, #0a0e27 0%, #050a1a 100%)",
      },
      backdropBlur: {
        xs: "2px",
      },
    },
  },
  plugins: [],
};
