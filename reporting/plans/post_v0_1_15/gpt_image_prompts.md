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
| 4 | README product-boundary diagram (replaces Mermaid) | 16:9 · 1600 × 900 | [`assets/product_boundary.png`](../../../assets/product_boundary.png) | **rendered 2026-05-04**, embedded in `README.md` "Product boundary" (replaced the in-section Mermaid) |
| 5 | README "why this exists" split-frame visual aid | 16:9 · 1600 × 900 | [`assets/why_this_exists.png`](../../../assets/why_this_exists.png) | **rendered 2026-05-04**, embedded in `README.md` "Why this exists" |
| 6 | README "how it feels to use" storyboard (replaces text dialogue) | 16:9 · 1600 × 900 | [`assets/how_it_feels.png`](../../../assets/how_it_feels.png) | **rendered 2026-05-04**, embedded in `README.md` "How it feels to use" (replaced the text dialogue block) |

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

## Visual language pin (applies to slots 4–6)

Slots 4–6 must match the established visual language of the
already-rendered slots 1–3 (`landing_hero.png`, `show_hn_card.png`,
`talk_slide_hero.png`). The shared rules:

**Colour palette — exactly two colours, no others.**

- **Background.** Warm off-white / cream / parchment, approximately
  `#F4EFE7`. NOT pure white. Subtle warm tint, identical across the
  whole canvas.
- **Accent.** A single deep dark teal-green, approximately `#1A3936`
  — reads as "dark teal" or "deep forest with a blue-green
  undertone". NOT black. NOT navy. NOT pure green. Used for every
  line, label, icon stroke, arrow, filled shape, and divider.
- **No third colour.** No greys, no gradients, no shadows, no
  glow, no tonal variation, no halftones. Solid filled shapes use
  the same accent colour as strokes.

**Typography.** Humanist sans-serif (Inter / DM Sans / Söhne or
similar). Medium weight for body labels, semibold for emphasis.
Monospace only inside CLI tags.

**Iconography (must match existing renders).**

- User person-glyph: filled circle head + rounded torso shape, no
  facial features (as in `show_hn_card.png`, `talk_slide_hero.png`).
- Agent operator-glyph: a small filled circle inside a thin ring (a
  sensor/operator symbol, as in `landing_hero.png`). NOT
  anthropomorphic, NOT a robot, NOT a face.
- Speech bubble: rounded rectangle with a small triangular tail.
- SQLite database: stack of three thin rounded ovals/discs
  (cylinder).
- JSONL audit log / paper: small rounded rectangle with three short
  horizontal lines inside.
- Keyring/config: simple key glyph (round bow + two rectangular
  teeth).
- CLI tag: small rounded rectangle, thin accent stroke, monospace
  text inside (as in the `> hai daily` terminal in
  `show_hn_card.png`).
- Wearable watch: generic geometric rectangle with rounded crown
  and two strap stubs. NOT branded.
- All icons use thin strokes (~1.5px equivalent) and rounded
  corners (~6–8px radius).
- Boxes/containers are rounded-corner rectangles with thin accent
  strokes (matches the box style in `landing_hero.png`).

**Layout discipline.**

- Generous whitespace at all four canvas edges (≥80px equivalent at
  1600×900).
- Flat 2D only. No 3D, no isometric, no perspective tricks.
- Solid arrows for permitted/active flows; dashed arrows for
  refused, read-only, or "considered but not chosen" flows.

If the prompt below conflicts with this pin, the pin wins. Re-render
the prompt rather than letting a slot drift outside the visual
language.

## Slot 4 — README product-boundary diagram

**Target.** In-section product-boundary diagram for `README.md`,
replacing the current Mermaid `flowchart TB`. The Mermaid renders
correctly on GitHub but reads as cramped technical detail; the
bitmap should land the boundary as a *story*, not a dependency
graph. The landing hero (slot 1) is editorial and stays at the top
of the README; this diagram is technical and lives under the
"Product boundary" heading.
**Aspect ratio.** 16:9 · **Output.** 1600 × 900 · **Filename.** `assets/product_boundary.png`

**Prompt (copy-paste ready).**

> Create a clean, editorial technical architecture diagram for a
> developer README. Aspect ratio 16:9, 1600×900 pixels. Match the
> existing visual language of the project: minimalist, Edward
> Tufte / Linear / Stripe-style, two colours only, flat 2D, no
> decorative effects.
>
> **Colour palette — use these exact colours, no others.** Background
> is a warm off-white / cream / parchment tone, approximately
> `#F4EFE7` (NOT pure white — subtle warm tint). Accent is a single
> deep dark teal-green, approximately `#1A3936` — every line, label,
> icon stroke, arrow, and filled element uses this one colour. No
> third colour. No greys. No gradients. No shadows.
>
> **Typography.** Humanist sans-serif (Inter / DM Sans / Söhne).
> Zone labels semibold; element labels medium. Black-equivalent text
> rendered in the dark-teal accent on cream.
>
> **Iconography.** Person/user icons are simple geometric: filled
> circle head + rounded torso, no facial features. The agent is a
> small filled circle inside a thin ring (sensor/operator glyph,
> matching `landing_hero.png`). SQLite database = stack of three
> thin rounded ovals. JSONL audit log = rounded rectangle with three
> short horizontal lines inside. Keyring = simple key glyph (round
> bow + two rectangular teeth). Validators = thin clipboard with a
> short checklist. Speech bubble = rounded rectangle with a
> triangular tail. Arrows are thin single-weight lines with simple
> solid arrowheads; solid for permitted flows, dashed for refused
> flows. All shapes have rounded corners (~6–8px radius) and thin
> strokes (~1.5px equivalent).
>
> **Layout — three labelled vertical bands left-to-right, separated
> by generous whitespace.**
>
> *Left band — "User & agent" zone.* A speech-bubble icon labelled
> "User conversation" connected via a curved dashed double-headed
> arrow to a small operator-glyph labelled "Shell-capable agent".
> Generous space between the two icons. Both sit at vertical
> centre.
>
> *Centre band — "hai · governed tool surface" zone.* A tall
> vertical rounded-rectangle gateway with a thin accent stroke and
> dashed top and bottom edges (match the dashed-rectangle style in
> the existing `landing_hero.png`), running approximately 70% of
> canvas height, centred vertically. Above the rectangle, a
> semibold label reads "hai · governed tool surface". Inside the
> rectangle, three small stacked icons labelled (top to bottom)
> "validate" (checkmark in a small circle), "gate" (a thin vertical
> bar), and "audit" (a magnifying glass over a dot). The rectangle
> is the visual focal point of the diagram.
>
> One thin solid arrow enters the gateway from the agent on the left
> and exits on the right side as "approved write". One additional
> dashed arrow attempts to bypass the gateway from the agent
> directly to the right band; that dashed arrow is intercepted at
> the gateway's left edge with a small ✕ glyph (matching the ✕ in
> `landing_hero.png`), indicating the refused write.
>
> *Right band — "Local substrates" zone.* A 2×2 grid of four small
> labelled rounded-rectangle boxes (matching the box style in
> `landing_hero.png`):
> - Top-left: SQLite cylinder icon labelled "SQLite state DB".
> - Top-right: paper-with-lines icon labelled "JSONL audit logs".
> - Bottom-left: key glyph labelled "keyring / config".
> - Bottom-right: clipboard glyph labelled "validators".
>
> Below the 2×2 grid, a thinner labelled strip reads "hai today ·
> explain · review · backup" in smaller text, with a single thin
> solid arrow returning leftward from this strip back to the agent
> in the left band (the read-only return path). Keep this return
> arrow visually subordinate to the main left-to-right flow.
>
> **Composition rules.** Generous whitespace at all four edges
> (≥80px equivalent at 1600×900). All icons and labels sharp; no
> grey halos against the cream background. The diagram reads as:
> *user talks · agent operates · hai gates · substrates persist ·
> reads return*.
>
> **Reference style.** Same visual family as `landing_hero.png` /
> `show_hn_card.png` / `talk_slide_hero.png` — warm cream
> background, single dark-teal accent, flat icons, thin
> humanist-sans labels, rounded-rectangle boxes.

**Negative prompt / exclusions.** No clinical or medical imagery
(doctors, scrubs, stethoscopes, hospitals, pills, IV bags, ECG
lines, prescription pads, heart symbols). No cloud, datacentre,
server-rack, network-globe, or hosted-service iconography. No
anthropomorphic robot, no humanoid AI face, no eye/surveillance
imagery. No multi-agent or swarm imagery. No pure white background.
No black ink — accent is dark teal, not black. No second accent
colour, no greys, no gradients, no shadows, no glow, no fantasy or
sci-fi lighting. No flames, sparks, or burst effects. No watermarks,
no fake logos, no decorative typography. No tiny illegible labels —
every label must be legible at GitHub's default README rendering
width. No 3D effects, no isometric projection — flat 2D only.

## Slot 5 — README "why this exists" split-frame

**Target.** Visual aid for the README's "Why this exists" section.
The section opens with the failure-mode framing (an agent asked to
be everything at once) and the resolution (agent + deterministic
runtime + audit chain). The visual should land that *contrast* in
one glance before the prose elaborates.
**Aspect ratio.** 16:9 · **Output.** 1600 × 900 · **Filename.** `assets/why_this_exists.png`

**Prompt (copy-paste ready).**

> Create a clean editorial split-frame technical illustration for a
> developer README. Aspect ratio 16:9, 1600×900 pixels. Two
> side-by-side panels of equal width, separated by a single thin
> vertical divider line in the accent colour at canvas-centre.
> Match the existing visual language of the project: minimalist,
> two-colour, Tufte-style, no decorative effects, flat 2D.
>
> **Colour palette — use these exact colours, no others.** Background
> is warm off-white / cream / parchment, approximately `#F4EFE7`
> (NOT pure white — subtle warm tint, identical across both
> panels). Accent is a single deep dark teal-green, approximately
> `#1A3936` — every line, label, icon stroke, arrow, and filled
> shape uses this one colour. No third colour. No greys. No
> gradients. No shadows. No tonal variation.
>
> **Typography.** Humanist sans-serif (Inter / DM Sans / Söhne).
> Each panel has a large semibold title centred at the top: "Agent
> does everything" (left panel) and "Agent + governed runtime"
> (right panel). Inside each panel, smaller medium-weight labels
> for elements. Beneath each panel, a smaller lighter-weight
> subtitle line.
>
> **Iconography.** The agent is the same operator-glyph used in
> `landing_hero.png` (a small filled circle inside a thin ring) —
> identical size and stroke weight across both panels. Boxes are
> rounded-rectangle pills with thin accent strokes (matching the
> box style in `landing_hero.png`). Arrows are thin single-weight
> lines with simple solid arrowheads.
>
> **Layout.**
>
> *Left panel — titled "Agent does everything".* At approximate
> centre: a single operator-glyph representing the agent.
> Surrounding it, an overlapping cluster of seven small
> thin-stroked rounded-rectangle pills (NOT circles — match the
> rounded-rectangle box convention of the existing renders). The
> pills overlap slightly at their edges, arranged in a roughly
> hexagonal/scattered pattern around the operator-glyph. Each pill
> carries one label: "chat", "memory", "interpret", "plan",
> "validate", "audit", "DB". Between every pair of overlapping
> pills (and between several pills and the operator-glyph), thin
> solid arrows or thin solid lines criss-cross in multiple
> directions, intersecting and overlapping. The visual feel is
> "tangled responsibility, no clean boundary". Do NOT make it
> scribbled or cartoon-chaotic — the lines remain thin, deliberate,
> and individually drawable; the *aggregate* effect is overlap and
> tangle, not noise. At the bottom of the panel, centred, a smaller
> subtitle in lighter weight reads "non-deterministic · no audit
> trail".
>
> *Right panel — titled "Agent + governed runtime".* On the left
> of the panel: the same operator-glyph (agent), positioned at
> vertical centre. To the right of the operator-glyph: a tall
> vertical rounded-rectangle gateway (thin accent stroke, dashed
> top and bottom edges to match the gateway in `landing_hero.png`)
> running about 65% of panel height, with the semibold label "hai
> · governed tool surface" centred above the rectangle. To the
> right of the gateway: a single tidy vertical column of five
> small rounded-rectangle boxes, evenly spaced top to bottom, each
> with a thin stroke and a centred medium-weight label. Each box
> contains a small glyph beside its label:
> 1. "typed state" — small SQLite-cylinder glyph.
> 2. "deterministic classifiers" — small bands-of-three-stripes glyph.
> 3. "policy rules" — small clipboard glyph.
> 4. "atomic commits" — small checkmark-in-circle glyph.
> 5. "audit log" — small paper-with-three-lines glyph.
>
> One thin solid arrow goes from the operator-glyph through the
> centre of the gateway, then branches once on the right side of
> the gateway into five thin parallel arrows that each connect to
> one of the five boxes. Every arrow is solid, parallel where
> possible, and uncrossed. At the bottom of the panel, centred, a
> smaller subtitle in lighter weight reads "deterministic ·
> reconstructable".
>
> **Composition rules.** The two panels must be visually balanced —
> same operator-glyph size, same label sizes, same vertical
> alignment of titles and subtitles. The contrast between the
> panels carries the entire message: tangled-overlap on the left,
> clean-parallel on the right. Both panels must remain *readable* —
> no scribbles, no purely abstract noise, every label legible
> including in the cluttered left panel. Generous whitespace at
> the canvas edges (≥80px equivalent at 1600×900). The vertical
> divider between panels is a single thin line in the accent
> colour.
>
> **Reference style.** Same visual family as `landing_hero.png` /
> `show_hn_card.png` / `talk_slide_hero.png` — warm cream
> background, single dark-teal accent, flat icons, thin
> humanist-sans labels, rounded-rectangle boxes.

**Negative prompt / exclusions.** No clinical/medical imagery, no
cloud/datacentre/server iconography, no anthropomorphic robot face,
no eye/surveillance imagery, no fantasy or dramatic lighting, no
flames or burst effects, no decorative gradients, no shadows, no
greys, no second accent colour, no logos, no watermarks, no pure
white background, no black ink (accent is dark teal). The chaos
panel must remain *readable* — no scribbles, no pencil-sketch
effect, no purely abstract noise; every label legible. Both panels'
titles and subtitles must be readable at the README's default
GitHub rendering width. No 3D, no isometric, flat 2D only. No
tonal variation in fills (no two-tone shading, no halftones).

## Slot 6 — README "how it feels to use" storyboard

**Target.** Replaces the text dialogue block in the README's "How
it feels to use" section. The dialogue communicates the
conversational arc but reads as filler in an otherwise dense
README; a single visual is more effective. The storyboard format
shows the agent invoking `hai` and reading back from `hai explain`
without making the user the operator.
**Aspect ratio.** 16:9 · **Output.** 1600 × 900 · **Filename.** `assets/how_it_feels.png`

**Prompt (copy-paste ready).**

> Create a clean editorial five-panel storyboard illustration for
> a developer README. Aspect ratio 16:9, 1600×900 pixels. Five
> horizontal panels of equal width separated by faint vertical
> accent-colour dividers, reading left-to-right as a temporal
> sequence. Match the existing visual language of the project:
> minimalist, two-colour, Tufte-style, no decorative effects,
> flat 2D.
>
> **Colour palette — use these exact colours, no others.**
> Background is warm off-white / cream / parchment, approximately
> `#F4EFE7` (NOT pure white — subtle warm tint). Accent is a single
> deep dark teal-green, approximately `#1A3936` — every line,
> label, icon stroke, arrow, and filled element uses this one
> colour. No third colour. No greys. No gradients. No shadows.
>
> **Typography.** Humanist sans-serif (Inter / DM Sans / Söhne).
> Across the top of all five panels, a thin labelled banner reads
> in semibold: "User experience is conversational. System
> architecture is not." Centred horizontally above the panel row,
> with a thin horizontal accent-colour line beneath it separating
> the banner from the panels. Each panel has a one-line label
> below the icon row, in medium weight. Speech-bubble contents are
> smaller and tucked inside the bubble shape.
>
> **Iconography (must match existing renders).** User =
> simple person-glyph (filled circle head + rounded torso shape, no
> facial features), as in `show_hn_card.png` and
> `talk_slide_hero.png`. Agent = the operator-glyph used in
> `landing_hero.png` (a small filled circle inside a thin ring).
> Speech bubbles = rounded rectangle with a small triangular tail
> (matches `show_hn_card.png`). CLI tags = small rounded
> rectangles with monospace text inside, thin-stroked in the
> accent colour, identical in style to the `> hai daily` terminal
> in `show_hn_card.png`. Wearable watch silhouette = a generic
> rectangular wearable face with a rounded crown and two strap
> stubs — geometric only, NOT a branded device. Database
> cylinder = stack of three thin rounded ovals. Bands diagram =
> three short horizontal stripes of differing length stacked
> vertically. Audit-trail/scroll = a small rectangle with three
> horizontal lines, partially unrolled at the bottom edge. All
> icons thin-stroked at ~1.5px equivalent, with rounded corners
> ~6px radius.
>
> **Layout — five panels left-to-right, equal width and equal
> height.**
>
> *Panel 1 — labelled "User asks" below the panel icon.* A small
> user person-glyph on the left of the panel, with a speech bubble
> extending up-and-right. Inside the speech bubble, in a smaller
> font, the text: "Plan today. I slept badly and my quads are
> sore."
>
> *Panel 2 — labelled "Agent reads the contract".* The agent
> operator-glyph centred in the panel, with a thin solid arrow
> extending up-and-right to a small CLI tag containing the
> monospace text "hai capabilities --json".
>
> *Panel 3 — labelled "Runtime gates and classifies".* A single
> tall vertical rounded-rectangle gateway in the centre of the
> panel, thin accent stroke, dashed top and bottom edges (match
> the gateway style in `landing_hero.png`). Above the gateway, the
> semibold label "hai · governed tool surface". Inside the
> gateway, three small stacked icons in vertical alignment: top —
> a downward arrow over the geometric watch silhouette (passive
> data pull); middle — the bands-diagram glyph (classify); bottom
> — the database-cylinder glyph with a small ✓ checkmark beside it
> (commit).
>
> *Panel 4 — labelled "Agent narrates".* The agent operator-glyph
> on the left, with a speech bubble extending up-and-right.
> Inside the speech bubble, in a smaller font: "easy run · sleep
> priority · lower stress load".
>
> *Panel 5 — labelled "User asks why".* On the left of the panel:
> a small user person-glyph with a single question mark "?"
> floating above. To its right, the agent operator-glyph, with a
> thin solid arrow from the agent to a small CLI tag containing
> the monospace text "hai explain". Below the CLI tag, the
> audit-trail/scroll glyph (small rectangle with horizontal lines,
> partially unrolled).
>
> **Composition rules.** All five panels equal width and equal
> height. Each panel is bordered only by the faint vertical
> dividers between adjacent panels — no top or bottom borders
> inside the panel row. Generous whitespace within each panel;
> icons sit at vertical-centre. The banner above the panels is
> the only top-level title. Generous whitespace at all four canvas
> edges (≥80px equivalent at 1600×900).
>
> **Reference style.** Same visual family as `landing_hero.png` /
> `show_hn_card.png` / `talk_slide_hero.png` — warm cream
> background, single dark-teal accent, flat icons, thin
> humanist-sans labels, rounded-rectangle boxes, monospace CLI
> tags identical in style to the `> hai daily` terminal in
> `show_hn_card.png`.

**Negative prompt / exclusions.** No clinical/medical imagery
(doctors, scrubs, stethoscopes, hospitals, pills, IV bags, ECG
lines, prescription pads, heart symbols). No cloud, datacentre,
server-rack, or hosted-service iconography. No anthropomorphic
robot face, no humanoid AI face, no eye/surveillance imagery. No
fantasy or dramatic lighting, no flames or burst effects, no
decorative gradients, no shadows, no halftone shading, no second
accent colour, no greys, no logos, no watermarks. No pure white
background, no black ink (accent is dark teal, not black). The
wearable watch silhouette must be a generic geometric outline —
NO Apple-watch / Garmin / Whoop / Fitbit branding, NO real-world
product references. No tiny illegible text — speech-bubble
contents and panel labels must remain readable at the README's
default GitHub rendering width. No 3D, no isometric — flat 2D
only.
