import sitemap from '@astrojs/sitemap';
import tailwindcss from '@tailwindcss/vite';
import { defineConfig } from 'astro/config';
import { editorApi } from './scripts/editor-integration.ts';

// Static output: every page is prerendered to HTML so unit/weapon pages are
// directly linkable and cacheable on the Cloudflare edge. Interactive tools
// (army builder, damage calculator, comparison) run entirely client-side.
export default defineConfig({
  output: 'static',
  // Production custom domain. Used for canonical links, OG/Twitter absolute
  // URLs and the generated sitemap — must match the deployed origin.
  site: 'https://wh40k-battlesector.crystalgametools.org',
  // Dev-only editor save API. The integration's middleware only attaches during
  // `astro dev`, so it has zero effect on the static production build.
  integrations: [
    editorApi(),
    sitemap({
      // Editor-only routes are stripped from dist before deploy; keep them out
      // of the sitemap too.
      filter: (page) => !page.includes('/editor'),
    }),
  ],
  vite: {
    plugins: [tailwindcss()],
  },
});
