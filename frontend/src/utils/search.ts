/** Catalog names are hyphenated (PokeAPI convention, e.g. "trick-room",
 * "rotom-wash") but displayed with the hyphen swapped for a space. Without
 * normalizing both sides the same way, typing what's on screen — "trick r" —
 * fails to match the stored "trick-room" the instant a space is typed where
 * the hyphen is. */
export function matchesSearch(name: string, query: string): boolean {
  const normalize = (s: string) => s.trim().toLowerCase().replace(/-/g, " ");
  const q = normalize(query);
  return !q || normalize(name).includes(q);
}
