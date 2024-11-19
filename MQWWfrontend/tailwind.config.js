/** @type {import('tailwindcss').Config} */
export default {
  content: ["./src/**/*.{html,js,svelte}"],
  theme: {
    extend: {
      // container: {
      //   center: true,
      //   padding: '1rem',
      //   // 明确覆盖默认的 max-width
      //   screens: {
      //     sm: '100%', // 对所有断点应用 100% 宽度
      //     md: '100%',
      //     lg: '100%',
      //     xl: '100%',
      //     '2xl': '100%',
      //   },
      // },
    },
  },
  plugins: [
      require('daisyui'),
  ],
  daisyui: {
    themes: ['light'], // false: only light + dark | true: all themes | array: specific themes like this ["light", "dark", "cupcake"]
    darkTheme: "dark", // name of one of the included themes for dark mode
    base: true, // applies background color and foreground color for root element by default
    styled: true, // include daisyUI colors and design decisions for all components
    utils: true, // adds responsive and modifier utility classes
    prefix: "", // prefix for daisyUI classnames (components, modifiers and responsive class names. Not colors)
    logs: true, // Shows info about daisyUI version and used config in the console when building your CSS
    themeRoot: ":root", // The element that receives theme color CSS variables
  },
}

