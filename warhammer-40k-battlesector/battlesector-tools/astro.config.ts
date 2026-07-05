import tailwindcss from '@tailwindcss/vite';
import { defineConfig } from 'astro/config';
import { editorApi } from './scripts/editor-integration.ts';

// Static output: every page is prerendered to HTML so unit/weapon pages are
// directly linkable and cacheable on the Cloudflare edge. Interactive tools
// (army builder, damage calculator, comparison) run entirely client-side.
export default defineConfig({
  output: 'static',
  site: 'https://battlesector-tools.pages.dev',
  // Dev-only editor save API. The integration's middleware only attaches during
  // `astro dev`, so it has zero effect on the static production build.
  integrations: [editorApi()],
  vite: {
    plugins: [tailwindcss()],
  },
});
