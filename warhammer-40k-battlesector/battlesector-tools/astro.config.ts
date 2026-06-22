import tailwindcss from '@tailwindcss/vite';
import { defineConfig } from 'astro/config';

// Static output: every page is prerendered to HTML so unit/weapon pages are
// directly linkable and cacheable on the Cloudflare edge. Interactive tools
// (army builder, damage calculator, comparison) run entirely client-side.
export default defineConfig({
  output: 'static',
  site: 'https://battlesector-tools.pages.dev',
  // The standalone weapons browser was removed in favour of unit-centric
  // loadout views; weapon detail pages remain. Redirect the old index so any
  // existing links resolve to the units database.
  redirects: {
    '/weapons': '/units',
  },
  vite: {
    plugins: [tailwindcss()],
  },
});
