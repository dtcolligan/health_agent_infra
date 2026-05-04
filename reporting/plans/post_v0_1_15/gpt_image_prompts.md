# GPT Images Prompt Notes

Three GPT Image renders ship with this docs pass under top-level
[`assets/`](../../../assets/). The prompts below are the source-of-truth
for re-rendering or iterating. Internal architecture docs continue to
use Mermaid because it is diffable, reviewable, and source-controlled —
the bitmaps are reserved for outward-facing public surfaces (README
hero, social card, talk slides), not for the canonical architecture
pages.

| Slot | Target | Aspect / output | Filename | Status |
|---|---|---|---|---|
| 1 | Public landing-page / README hero | 16:9 · 1600 × 900 | [`assets/landing_hero.png`](../../../assets/landing_hero.png) | **rendered 2026-05-04**, embedded in `README.md` |
| 2 | Show HN / Open Graph card | 1.91:1 · 1200 × 630 | [`assets/show_hn_card.png`](../../../assets/show_hn_card.png) | **rendered 2026-05-04**, referenced from `reporting/docs/launch/show_hn_draft.md` |
| 3 | Maintainer's-talk slide-deck hero | 16:9 · 1920 × 1080 | [`assets/talk_slide_hero.png`](../../../assets/talk_slide_hero.png) | **rendered 2026-05-04**, parked under `assets/` for talk decks (not currently embedded in any doc) |

The renders are kept verbatim from the GPT Image output — no editing,
crop, or recolouring. Re-running a prompt to iterate is fine; record
the new render date in this table and overwrite the file at its
canonical filename so links don't drift.

Do **not** embed these bitmaps in the canonical internal architecture
pages (`ARCHITECTURE.md`, `reporting/docs/architecture.md`,
`reporting/docs/explainability.md`) — those stay Mermaid so changes are
diffable.

## Diagrams Added Instead

| Target doc | Format | Why |
|---|---|---|
| `README.md` | Mermaid | Shows the user -> agent -> `hai` wrapper -> local state boundary without implying cloud services or medical authority. |
| `reporting/docs/architecture.md` | Mermaid | Shows both the host-agent journey and the runtime pipeline under the wrapper. |
| `reporting/docs/explainability.md` | Mermaid | Shows which persisted rows `hai explain` reads and what it deliberately does not recompute or write. |
| `reporting/docs/how_to_add_a_domain.md` | Mermaid | Shows the wiring blast radius for a new domain in a way that remains source-reviewable. |

## Slot 1 — Landing-page / README hero

**Target.** Top-of-README hero or future project website landing image.
Supplements the existing Mermaid wrapper diagram; does not replace it.
**Aspect ratio.** 16:9 · **Output.** 1600 × 900 · **Filename.** `assets/landing_hero.png`

**Prompt.**

> Create a clean editorial technical illustration for an open-source
> developer README. Aspect ratio 16:9. White or very light neutral
> background. Layout left to right: a "User conversation" speech-bubble
> icon on the left, a simple abstract "Shell-capable personal-health
> agent" operator icon in the center, a clearly labeled boundary layer
> marked "hai · governed tool surface" between agent and state, and on
> the right a small grid of labeled local-substrate boxes — "SQLite
> state DB", "JSONL audit logs", "keyring / config", "validators". Show
> one prominent rejected/forbidden arrow from the agent attempting to
> write directly to SQLite, crossed out by the `hai` boundary, and one
> accepted arrow going through `hai`. Restrained line art, muted blues
> and greys with one accent color, generous whitespace, readable labels
> in a humanist sans-serif. The agent is an abstract operator figure —
> not a robot, not a doctor, not anthropomorphic.

**Negative prompt / exclusions.** No doctors, stethoscopes, hospitals,
pills, diagnosis imagery, prescription pads. No cloud servers, server
racks, datacenters, network globes. No surveillance cameras or eyes. No
multi-agent swarm or many-figures-talking-to-each-other imagery. No
brain or neural-network imagery. No autonomous-treatment language, no
dramatic dark lighting, no fantasy / sci-fi tropes, no unreadable tiny
text, no decorative gradients, no logos, no watermarks.

## Slot 2 — Show HN / Open Graph card

**Target.** Thumbnail/header for Show HN, X, LinkedIn, etc. Catches the
eye in a feed and telegraphs "local + governed" in one glance.
**Aspect ratio.** 1.91:1 · **Output.** 1200 × 630 · **Filename.** `assets/show_hn_card.png`

**Prompt.**

> A clean technical announcement-card illustration for a developer-tools
> launch post. Aspect ratio 1.91:1, intended for social sharing. Use a
> soft off-white background with a single accent color (deep teal or
> muted navy). Center: a stylized terminal window with the prompt
> `hai daily` visible, wrapped by a thin labeled boundary that reads
> "governed local runtime". To the left of the terminal: a small
> abstract person icon with a dialog bubble. To the right: a labeled
> local SQLite cylinder with a simple lock or shield motif suggesting
> "audit chain". Below the illustration, large readable headline text in
> a humanist sans-serif: "Health Agent Infra" with a smaller subtitle
> "Local plugin / runtime wrapper around a personal-health agent". The
> composition should remain readable at 600px wide. No people in
> clinical settings, no medical imagery whatsoever, no cloud or
> server-rack iconography.

**Negative prompt / exclusions.** No clinical imagery (doctors, scrubs,
stethoscopes, hospitals, pills, IV bags, ECG lines, prescription pads).
No cloud, datacenter, server rack, network globe, or hosted-service
imagery. No anthropomorphic robot, no humanoid AI face, no
eye/surveillance imagery. No dramatic gradients, no fantasy lighting,
no flames or burst effects. Headline must be readable at 600px wide; no
decorative typography that obscures text. No watermarks, no fake logos.

## Slot 3 — Maintainer's-talk slide-deck hero

**Target.** Opening slide of a talk / lightning talk. Designed to
project legibly at distance from the back of a room. More open layout,
larger labels, less detail than the README hero.
**Aspect ratio.** 16:9 · **Output.** 1920 × 1080 · **Filename.** `assets/talk_slide_hero.png`

**Prompt.**

> A minimal, projector-friendly slide-deck hero illustration. Aspect
> ratio 16:9, designed to be readable from the back of a 30-person
> room. Very generous whitespace, three-zone horizontal layout: "User"
> (small icon, left), "Agent" (slightly larger abstract operator
> figure, center-left), "hai · governed wrapper" (a clear vertical
> boundary layer through the middle), "Local state" (right zone with a
> single SQLite cylinder + a simple JSONL "audit log" sheet icon).
> Labels are large — at least 1/24 the height of the canvas — so they
> remain legible at projection distance. One thick arrow from User to
> Agent (conversational), one thin arrow from Agent through hai to
> Local state (governed write), and one dashed broken arrow from Agent
> to Local state that does not reach across the boundary (the
> refusal). Use a single muted accent color plus dark grey on
> near-white. The aesthetic is "Edward Tufte" rather than "marketing
> brochure".

**Negative prompt / exclusions.** No clinical/medical imagery. No
cloud, server, datacenter iconography. No multi-agent or swarm
imagery. No anthropomorphic robot or AI face. No dense detail, no
small text under 60px equivalent, no decorative shading or gradients,
no animation effects baked into the image, no logos, no watermarks.
Must remain legible when projected; do not make the labels stylized to
the point of being hard to read.
