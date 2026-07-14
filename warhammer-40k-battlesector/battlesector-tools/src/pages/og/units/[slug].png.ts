import type { APIRoute } from 'astro';
import { getUnit, unitSlug, units } from '../../../lib/data';
import { unitCard } from '../../../lib/og/cards';
import { renderCard } from '../../../lib/og/render';

export function getStaticPaths() {
  return units.map((u) => ({ params: { slug: unitSlug(u) }, props: { id: u.id } }));
}

export const GET: APIRoute = async ({ props }) => {
  const unit = getUnit((props as { id: number }).id);
  if (!unit) return new Response('Not found', { status: 404 });
  const png = await renderCard(await unitCard(unit));
  return new Response(png, {
    headers: {
      'Content-Type': 'image/png',
      'Cache-Control': 'public, max-age=31536000, immutable',
    },
  });
};
