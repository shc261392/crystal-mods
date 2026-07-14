/**
 * Build-time Open Graph card rendering.
 *
 * Satori turns a lightweight virtual DOM into SVG, then resvg rasterises it to a
 * PNG (Discord, Facebook, X and LinkedIn all require a raster og:image — they do
 * NOT render SVG). Cards are generated during `astro build` and emitted as static
 * assets, so there is zero runtime cost on the Cloudflare edge.
 */
import { readFile } from 'node:fs/promises';
import { createRequire } from 'node:module';
import { Resvg } from '@resvg/resvg-js';
import satori from 'satori';

const require = createRequire(import.meta.url);

export const OG_WIDTH = 1200;
export const OG_HEIGHT = 630;

const FONT_FILES = {
  400: '@fontsource/inter/files/inter-latin-400-normal.woff',
  600: '@fontsource/inter/files/inter-latin-600-normal.woff',
  700: '@fontsource/inter/files/inter-latin-700-normal.woff',
} as const;

let fontsPromise: Promise<
  Array<{ name: string; data: Buffer; weight: 400 | 600 | 700; style: 'normal' }>
> | null = null;

function loadFonts() {
  if (!fontsPromise) {
    fontsPromise = Promise.all(
      (Object.entries(FONT_FILES) as Array<[string, string]>).map(async ([weight, spec]) => ({
        name: 'Inter',
        data: await readFile(require.resolve(spec)),
        weight: Number(weight) as 400 | 600 | 700,
        style: 'normal' as const,
      })),
    );
  }
  return fontsPromise;
}

// --- lightweight hyperscript ------------------------------------------------
// Satori consumes React-element-shaped objects. We build them without JSX so the
// module needs no extra tooling. Every element carries an explicit `display`
// because Satori requires it on any container with multiple children.

export type OGChild = OGNode | string | number | false | null | undefined;
export interface OGNode {
  type: string;
  props: { style?: Record<string, unknown>; children?: unknown; [k: string]: unknown };
}

export function h(
  type: string,
  props: (Record<string, unknown> & { style?: Record<string, unknown> }) | null,
  ...children: OGChild[]
): OGNode {
  const flat = children.flat().filter((c) => c !== false && c != null) as OGChild[];
  // Satori requires an explicit `display` on any container with children; default
  // divs to flex while letting an explicit style override it.
  const style =
    type === 'div' ? { display: 'flex', ...(props?.style ?? {}) } : { ...(props?.style ?? {}) };
  return {
    type,
    props: {
      ...(props ?? {}),
      style,
      children: flat.length === 1 ? flat[0] : flat,
    },
  };
}

export async function renderCard(node: OGNode): Promise<ArrayBuffer> {
  const svg = await satori(node as Parameters<typeof satori>[0], {
    width: OG_WIDTH,
    height: OG_HEIGHT,
    fonts: await loadFonts(),
  });
  const resvg = new Resvg(svg, {
    fitTo: { mode: 'width', value: OG_WIDTH },
    font: { loadSystemFonts: false },
  });
  const png = resvg.render().asPng();
  const out = new ArrayBuffer(png.byteLength);
  new Uint8Array(out).set(png);
  return out;
}
