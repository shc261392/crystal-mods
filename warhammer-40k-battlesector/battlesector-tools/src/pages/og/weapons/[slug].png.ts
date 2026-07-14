import type { APIRoute } from 'astro';
import { getWeapon, weaponSlug, weapons } from '../../../lib/data';
import { weaponCard } from '../../../lib/og/cards';
import { renderCard } from '../../../lib/og/render';

export function getStaticPaths() {
  return weapons.map((w) => ({ params: { slug: weaponSlug(w) }, props: { id: w.id } }));
}

export const GET: APIRoute = async ({ props }) => {
  const weapon = getWeapon((props as { id: number }).id);
  if (!weapon) return new Response('Not found', { status: 404 });
  const png = await renderCard(await weaponCard(weapon));
  return new Response(png, {
    headers: {
      'Content-Type': 'image/png',
      'Cache-Control': 'public, max-age=31536000, immutable',
    },
  });
};
