# Contributing to Cevian

## Adding a problem by hand

Problems are data. Each one is a JSON file, `data/problems/<id>.json`, checked against [`schema/problem.schema.json`](schema/problem.schema.json). You never need to touch the site's code to add one.

You need Node 20 or later. Run `npm install` once to get the validator's one dependency.

### 1. Write the JSON

Copy a problem of the same type and edit it. [`data/problems/the-13-14-15-triangle.json`](data/problems/the-13-14-15-triangle.json) is an answer problem and [`data/problems/vieta-leap.json`](data/problems/vieta-leap.json) is a proof problem.

```json
{
  "id": "circle-in-the-square",
  "title": "Circle in the Square",
  "kyu": 5,
  "topic": "G",
  "subtopics": ["coordinate-bash", "tangency"],
  "type": "answer",
  "status": "draft",
  "statement": "Square $ABCD$ has side length $10$. ...",
  "answer_format": "rational",
  "answer_hash": "a7169a50",
  "hints": ["The centre lies on the perpendicular bisector of $AB$. ..."],
  "solution": "Put $A=(0,0)$, $B=(10,0)$ ...",
  "provenance": { "kind": "original", "author": "kevinvariant" },
  "stats": { "solves": 0, "attempts": 0, "liked": 0 }
}
```

- **`id`** is kebab-case and permanent. It's the URL (`#p-<id>`), the file name and the salt in the answer hash, so it can never be renamed.
- **`kyu`** runs from 8 (warm-up) to 1 (IMO P3/P6). **`topic`** is `A`, `C`, `G` or `N`.
- **`subtopics`** are technique slugs. Once task 03 publishes `data/taxonomy.json`, the validator checks them against it.
- **Text fields** (`statement`, `hints`, `solution`) hold Markdown with LaTeX between `$…$` or `$$…$$`. In JSON every backslash is doubled: write `\\frac{a}{b}` to get `\frac{a}{b}`. The site currently renders paragraphs, separated by a blank line (`\n\n`), and nothing else from Markdown.
- **`hints`**: one to three, gentlest first.
- **Answer problems** need `answer_hash` and `answer_format` (`integer_0_999`, `integer`, `rational` or `expression`). The plain answer never goes in the file.
- **Proof problems** need a `rubric` of `{ "marks": n, "criterion": "..." }` items totalling 7.
- **`provenance.kind`** is `original` or `classical`. A classical problem also needs a `source`, such as `"IMO 1988 P6"`. A generated problem records its `pipeline_run`. Contest problem texts stay out of this repo (see rule 1 in [`tasks/README.md`](tasks/README.md)).
- **`status`** starts as `draft`, which keeps the problem out of every list. `beta` and `ranked` problems are listed. They also need a `verification` report ID from the verification gate (task 05). Until that gate exists, a hand-checked problem uses `"verification": "seed-unverified"`, the marker the 21 seed problems carry, and task 05 replaces it with a real report ID. `retired` problems drop out of lists, but their pages still work.
- **`stats`** stay at zero. Only real data goes there.

### 2. Hash the answer

```bash
node scripts/hash-answer.mjs circle-in-the-square 25/4
```

It prints the canonical form (`6.25`) and the hash (`a7169a50`). The script uses the same `canon()` and `fnv()` as the site, from `js/lib/answers.js`. A fraction, a decimal and an integer that are equal all give the same hash, so `25/4`, `6.25` and `6.250` are all accepted.

### 3. Build and validate

```bash
node scripts/build-index.mjs
```

```bash
node scripts/validate.mjs
```

`build-index` rewrites `data/index.json`, the small manifest that the problem list loads. `validate` checks every file against the schema. It also checks that each ID matches its file name and is unique, that rubrics total 7, that any figure exists, and that `data/index.json` is up to date. It prints each error with its file and exits non-zero. GitHub Actions runs it on every pull request.

Commit the problem file and `data/index.json` together.

## Running the site locally

The site is static files, with no build step. Serve the folder and open it:

```bash
python -m http.server 8000
```

Then go to http://localhost:8000. The site uses only relative URLs, so it works the same at `kevinvariant08.github.io/cevian/`.

## How the code is laid out

| Path | What it holds |
|---|---|
| `index.html` | The shell: head, header, `<main>`, footer and one module script |
| `css/site.css` | All styles, with light and dark tokens |
| `js/app.js` | The router (`#home`, `#problems`, `#p-<id>`, `#duel`, `#profile`, `#leaderboard`) and boot |
| `js/views/*.js` | One module per view |
| `js/lib/answers.js` | `canon`, `fnv` and `check`, shared with the scripts |
| `js/lib/store.js` | Progress in `localStorage` under `mathwars:v1` |
| `js/lib/problems.js` | Loads `data/index.json`, and loads each full problem only when it's needed |
| `js/lib/ranks.js`, `tex.js`, `ui.js` | Belts and ranks, MathJax, shared page helpers |

## Caching

Cevian shares its origin with Kevinvariant, whose service worker (`/sw.js`) controls these pages too:

- **JS, CSS and JSON** carry no `?v=`, so the service worker fetches them network-first and a deploy shows up at once. Don't add `?v=` to one file. The service worker would cache that file forever, while the modules it imports stayed network-first, so old and new code would mix.
- **SVG and other images** are cached forever, whatever their URL. A changed figure needs a new file name.
- Every `localStorage` key starts with `mathwars:`. The prefix predates the rename to Cevian and stays, so existing progress survives.
