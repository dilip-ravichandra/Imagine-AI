import { extendTheme, type ThemeConfig } from '@chakra-ui/react';

const config: ThemeConfig = {
  initialColorMode: 'dark',
  useSystemColorMode: false,
};

const theme = extendTheme({
  config,
  styles: {
    global: {
      'html, body': {
        bg: '#080B0A',
        color: '#F4F7F0',
        fontFamily: "'Inter', 'Segoe UI', system-ui, sans-serif",
        margin: 0,
        padding: 0,
        minHeight: '100vh',
      },
      '*': {
        boxSizing: 'border-box',
      },
      '::-webkit-scrollbar': {
        width: '6px',
      },
      '::-webkit-scrollbar-track': {
        bg: '#080B0A',
      },
      '::-webkit-scrollbar-thumb': {
        bg: '#2A3A2C',
        borderRadius: '3px',
      },
      '::-webkit-scrollbar-thumb:hover': {
        bg: '#3A4A3C',
      },
    },
  },
  colors: {
    brand: {
      50: '#f0ffe0',
      100: '#d4ffaa',
      200: '#c5ff6b',
      300: '#B7FF35',
      400: '#8DDB39',
      500: '#B7FF35',
      600: '#8DDB39',
      700: '#5FA020',
      800: '#3A6A10',
      900: '#1A3A05',
    },
    surface: {
      bg: '#080B0A',
      card: '#111713',
      elevated: '#182019',
      sidebar: '#0D120E',
      input: '#0F1A11',
      hover: '#1A2A1C',
      border: '#2A3A2C',
    },
    text: {
      primary: '#F4F7F0',
      secondary: '#A5B1A7',
      muted: '#6B7B6D',
    },
  },
  components: {
    Button: {
      variants: {
        brand: {
          bg: '#B7FF35',
          color: '#080B0A',
          fontWeight: '600',
          _hover: {
            bg: '#8DDB39',
            transform: 'translateY(-1px)',
          },
          _active: {
            bg: '#6FBB20',
            transform: 'translateY(0)',
          },
          transition: 'all 0.2s ease',
        },
        ghost: {
          color: '#A5B1A7',
          _hover: {
            bg: '#1A2A1C',
            color: '#F4F7F0',
          },
        },
        outline: {
          borderColor: '#2A3A2C',
          color: '#B7FF35',
          _hover: {
            bg: '#1A2A1C',
            borderColor: '#B7FF35',
          },
        },
      },
    },
    Input: {
      variants: {
        filled: {
          field: {
            bg: '#0F1A11',
            border: '1px solid #2A3A2C',
            color: '#F4F7F0',
            _hover: { bg: '#1A2A1C', borderColor: '#3A4A3C' },
            _focus: { bg: '#1A2A1C', borderColor: '#B7FF35', boxShadow: '0 0 0 1px #B7FF35' },
            _placeholder: { color: '#6B7B6D' },
          },
        },
      },
      defaultProps: {
        variant: 'filled',
      },
    },
    Select: {
      variants: {
        filled: {
          field: {
            bg: '#0F1A11',
            border: '1px solid #2A3A2C',
            color: '#F4F7F0',
            _hover: { bg: '#1A2A1C' },
            _focus: { borderColor: '#B7FF35' },
          },
        },
      },
      defaultProps: {
        variant: 'filled',
      },
    },
    Tabs: {
      variants: {
        'soft-rounded': {
          tab: {
            color: '#A5B1A7',
            _selected: {
              bg: '#B7FF35',
              color: '#080B0A',
              fontWeight: '600',
            },
          },
        },
      },
    },
  },
});

export default theme;
