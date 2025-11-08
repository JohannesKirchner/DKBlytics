import tailwindcss from '@tailwindcss/vite';
import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';

export default defineConfig({
	plugins: [tailwindcss(), sveltekit()],
  server: {
    proxy: {
      // redirect any request that starts with /api
      '/api': {
        target: 'http://localhost:8000', // backend URL
        changeOrigin: true,
      },
    },
  },
});
