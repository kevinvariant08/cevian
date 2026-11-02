// Subtopic names and one-line definitions from data/taxonomy.json. The file is 58 KB, so it loads only when a
// problem page first shows what it taught; until then, and if it fails, names come from the slug.
const entries = new Map();   // slug -> { id, topic, definition }

let loading = null;
export function loadTaxonomy() {
  if (!loading) loading = fetch(new URL("../../data/taxonomy.json", import.meta.url))
    .then((res) => (res.ok ? res.json() : {}))
    .then((t) => { for (const x of [...(t.techniques || []), ...(t.configurations || [])]) if (x && x.id) entries.set(x.id, x); })
    .catch(() => { loading = null; });
  return loading;
}

const humanise = (slug) => { const s = slug.replace(/-/g, " "); return s[0].toUpperCase() + s.slice(1); };
export const subtopicName = (slug) => (entries.get(slug) && entries.get(slug).name) || humanise(slug);
export const subtopicDefinition = (slug) => (entries.get(slug) && entries.get(slug).definition) || "";
