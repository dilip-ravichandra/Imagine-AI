import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react-swc';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    // Proxy API requests to backend Modal URL (replace with actual URL later)
    proxy: {
      '/api': {
        target: 'https://your-modal-backend-url.com',
        changeOrigin: true,
        secure: false,
        rewrite: (path) => path.replace(/^\/api/, ''),
      },
    },
  },
});
