import tailwindcss from '@tailwindcss/vite';
import { defineConfig } from 'astro/config';

// Static output: every page is prerendered to HTML so unit/weapon pages are
// directly linkable and cacheable on the Cloudflare edge. Interactive tools
// (army builder, damage calculator, comparison) run entirely client-side.
export default defineConfig({
  output: 'static',
  site: 'https://battlesector-tools.pages.dev',
  vite: {
    plugins: [tailwindcss()],
  },
});
