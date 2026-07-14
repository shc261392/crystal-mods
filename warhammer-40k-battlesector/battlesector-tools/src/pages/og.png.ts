import type { APIRoute } from 'astro';
import { defaultCard } from '../lib/og/cards';
import { renderCard } from '../lib/og/render';

export const GET: APIRoute = async () => {
  const png = await renderCard(
    defaultCard(
      'Battlesector Tools',
      'Browse units, weapons and abilities, build army lists and calculate damage for Warhammer 40,000: Battlesector.',
    ),
  );
  return new Response(png, {
    headers: {
      'Content-Type': 'image/png',
      'Cache-Control': 'public, max-age=86400',
    },
  });
};
