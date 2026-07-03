/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{vue,js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        // "Precision Authority" design system used by Dashboard + Review views
        'surface':                   '#f8f9ff',
        'surface-bright':            '#f8f9ff',
        'surface-dim':               '#cbdbf5',
        'surface-container-lowest':  '#ffffff',
        'surface-container-low':     '#eff4ff',
        'surface-container':         '#e5eeff',
        'surface-container-high':    '#dce9ff',
        'surface-container-highest': '#d3e4fe',
        'surface-variant':           '#d3e4fe',
        'on-surface':                '#0b1c30',
        'on-surface-variant':        '#444748',
        'on-background':             '#0b1c30',
        'primary':                   '#000000',
        'on-primary':                '#ffffff',
        'primary-container':         '#1c1b1b',
        'secondary':                 '#006d35',
        'on-secondary':              '#ffffff',
        'secondary-container':       '#8df9a8',
        'on-secondary-container':    '#007439',
        'tertiary-fixed-dim':        '#ffb77d',
        'outline':                   '#747878',
        'outline-variant':           '#c4c7c7',
        'error':                     '#ba1a1a',
        'error-container':           '#ffdad6',
        'on-error-container':        '#93000a',
      },
      borderRadius: {
        DEFAULT: '0.125rem',
        lg:      '0.25rem',
        xl:      '0.5rem',
        full:    '0.75rem',
      },
      fontFamily: {
        headline: ['Manrope', 'sans-serif'],
        display:  ['Manrope', 'sans-serif'],
        body:     ['Inter', 'sans-serif'],
        label:    ['Inter', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
