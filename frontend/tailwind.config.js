/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        berry: {
          50:  "#f5f0ff",
          100: "#ede0ff",
          200: "#dbc5ff",
          300: "#c09aff",
          400: "#a06aff",
          500: "#8040f5",
          600: "#6b25e0",
          700: "#571bbd",
          800: "#481a99",
          900: "#3b177a",
          950: "#250d55",
        },
        ink: {
          50:  "#f0f0f8",
          100: "#ddddf0",
          200: "#c0c0e3",
          300: "#9898cf",
          400: "#7474b8",
          500: "#5a5aa5",
          600: "#484889",
          700: "#3b3b70",
          800: "#22213f",
          900: "#16152a",
          950: "#0d0c1a",
        },
      },
      fontFamily: {
        sans: ["'DM Sans'", "system-ui", "sans-serif"],
        mono: ["'JetBrains Mono'", "monospace"],
      },
      animation: {
        "pulse-slow": "pulse 3s cubic-bezier(0.4,0,0.6,1) infinite",
        "spin-slow": "spin 8s linear infinite",
        "fade-up": "fadeUp 0.5s ease forwards",
        "slide-in": "slideIn 0.4s ease forwards",
        "shimmer": "shimmer 1.8s infinite",
        "glow": "glow 2s ease-in-out infinite alternate",
      },
      keyframes: {
        fadeUp: {
          "0%": { opacity: 0, transform: "translateY(16px)" },
          "100%": { opacity: 1, transform: "translateY(0)" },
        },
        slideIn: {
          "0%": { opacity: 0, transform: "translateX(-16px)" },
          "100%": { opacity: 1, transform: "translateX(0)" },
        },
        shimmer: {
          "0%": { backgroundPosition: "-200% 0" },
          "100%": { backgroundPosition: "200% 0" },
        },
        glow: {
          "0%": { boxShadow: "0 0 20px rgba(128, 64, 245, 0.3)" },
          "100%": { boxShadow: "0 0 40px rgba(128, 64, 245, 0.7)" },
        },
      },
      backgroundImage: {
        "grid-berry": "linear-gradient(rgba(128,64,245,0.07) 1px, transparent 1px), linear-gradient(to right, rgba(128,64,245,0.07) 1px, transparent 1px)",
        "shimmer-gradient": "linear-gradient(90deg, transparent 0%, rgba(128,64,245,0.15) 50%, transparent 100%)",
      },
      backgroundSize: {
        "grid": "40px 40px",
      },
      boxShadow: {
        "berry": "0 0 30px rgba(128, 64, 245, 0.25)",
        "berry-lg": "0 0 60px rgba(128, 64, 245, 0.35)",
        "card": "0 1px 3px rgba(0,0,0,0.4), 0 0 0 1px rgba(255,255,255,0.05)",
        "card-hover": "0 4px 20px rgba(0,0,0,0.5), 0 0 0 1px rgba(128,64,245,0.3)",
      },
    },
  },
  plugins: [],
};
