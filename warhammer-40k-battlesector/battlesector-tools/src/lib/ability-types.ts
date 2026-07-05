export interface Ability {
  id: number;
  title: string;
  icon?: string;
  description: string;
  kind: 'active' | 'passive';
  actionPoints: number;
  cooldown: number;
  /** Player field-test note (not in game data). Curated locally via the editor. */
  notes?: string;
}
