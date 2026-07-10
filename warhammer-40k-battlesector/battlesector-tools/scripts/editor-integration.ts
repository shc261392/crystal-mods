import path from 'node:path';
/**
 * Dev-only editor API integration.
 *
 * Adds a tiny middleware to the Astro/Vite dev server that lets the local
 * editor pages persist curated edits straight into the git-tracked JSON under
 * `src/data/`. The `astro:server:setup` hook only runs during `astro dev`, so
 * this endpoint never exists in the static production build.
 *
 * Contract:
 *   POST /__editor/save   body: { target, id, patch }  -> { ok, changed }
 *   GET  /__editor/health                              -> { ok: true }
 */
import type { AstroIntegration } from 'astro';
import { type EditorTarget, applyPatch } from './editor-store.ts';

const SAVE_ROUTE = '/__editor/save';
const HEALTH_ROUTE = '/__editor/health';
const VALID_TARGETS: EditorTarget[] = ['unit', 'weapon', 'ability'];

// Files the editor modifies — must not trigger HMR reload during edit sessions
const EDITOR_MANAGED_FILES = [
  path.join('src', 'data', 'units.json'),
  path.join('src', 'data', 'weapons.json'),
  path.join('src', 'data', 'ability-overrides.source.json'),
  path.join('src', 'data', 'abilities.json'),
  path.join('src', 'lib', 'ability-types.ts'),
  path.join('src', 'lib', 'unit-abilities.ts'),
];

function readBody(req: import('node:http').IncomingMessage): Promise<string> {
  return new Promise((resolve, reject) => {
    const chunks: Buffer[] = [];
    req.on('data', (c: Buffer) => chunks.push(c));
    req.on('end', () => resolve(Buffer.concat(chunks).toString('utf8')));
    req.on('error', reject);
  });
}

function sendJson(res: import('node:http').ServerResponse, status: number, payload: unknown): void {
  const body = JSON.stringify(payload);
  res.statusCode = status;
  res.setHeader('content-type', 'application/json; charset=utf-8');
  res.end(body);
}

export function editorApi(): AstroIntegration {
  return {
    name: 'battlesector-editor-api',
    hooks: {
      'astro:server:setup': ({ server, logger }) => {
        // Prevent HMR reload when editor saves to these files
        const unwatchPaths = EDITOR_MANAGED_FILES.map((p) => path.resolve(process.cwd(), p));
        server.watcher.unwatch(unwatchPaths);

        server.middlewares.use((req, res, next) => {
          const url = req.url ?? '';

          if (req.method === 'GET' && url.startsWith(HEALTH_ROUTE)) {
            sendJson(res, 200, { ok: true });
            return;
          }

          if (req.method !== 'POST' || !url.startsWith(SAVE_ROUTE)) {
            next();
            return;
          }

          void (async () => {
            try {
              const raw = await readBody(req);
              const parsed = JSON.parse(raw || '{}') as {
                target?: string;
                id?: string | number;
                patch?: Record<string, unknown>;
              };

              const target = parsed.target as EditorTarget;
              if (!VALID_TARGETS.includes(target)) {
                sendJson(res, 400, { ok: false, message: `Invalid target: ${parsed.target}` });
                return;
              }
              if (parsed.id === undefined || parsed.id === null || parsed.id === '') {
                sendJson(res, 400, { ok: false, message: 'Missing id' });
                return;
              }
              if (!parsed.patch || typeof parsed.patch !== 'object') {
                sendJson(res, 400, { ok: false, message: 'Missing patch' });
                return;
              }

              const result = applyPatch(target, parsed.id, parsed.patch);
              logger.info(
                `saved ${result.target} ${result.id} (${result.changed.join(', ') || 'no-op'})`,
              );
              sendJson(res, result.ok ? 200 : 404, result);
            } catch (err) {
              const message = err instanceof Error ? err.message : String(err);
              logger.error(`editor save failed: ${message}`);
              sendJson(res, 500, { ok: false, message });
            }
          })();
        });

        logger.info('editor API: POST /__editor/save (dev only)');
        logger.info(`editor API: unwatched ${unwatchPaths.length} files to prevent HMR reload`);
      },
    },
  };
}
