# GPT Images Prompt Notes

No generated bitmap images were added in this docs pass.

Reason: the useful visuals are technical architecture and audit-chain maps that
need to stay versioned, diffable, and reviewable in Markdown. Mermaid is the
better format for the current internal docs.

## Diagrams Added Instead

| Target doc | Format | Why |
|---|---|---|
| `README.md` | Mermaid | Shows the user -> agent -> `hai` wrapper -> local state boundary without implying cloud services or medical authority. |
| `reporting/docs/architecture.md` | Mermaid | Shows both the host-agent journey and the runtime pipeline under the wrapper. |
| `reporting/docs/explainability.md` | Mermaid | Shows which persisted rows `hai explain` reads and what it deliberately does not recompute or write. |
| `reporting/docs/how_to_add_a_domain.md` | Mermaid | Shows the wiring blast radius for a new domain in a way that remains source-reviewable. |

## Optional Future Public Asset

Use only if a future public landing page needs a bitmap hero/overview image.
Do not use this image inside the current internal architecture docs.

Target doc: future public website or launch page, not current internal docs.

Intended caption: "A host agent operates personal-health workflows through a
governed local runtime wrapper."

Prompt for GPT Images:

> Create a clean editorial technical illustration for an open-source developer
> README. Aspect ratio 16:9. White or very light neutral background. Layout left
> to right: "User conversation" on the left, "Shell-capable personal-health
> agent" in the center, "hai governed tool surface" as a clear boundary layer,
> and "Local state" on the right with small labeled boxes for SQLite, JSONL
> audit logs, keyring/config, and validation. Use restrained line art, muted
> colors, readable labels, and no decorative gradients. Make the agent a simple
> abstract operator icon, not a robot doctor. Emphasize that the agent cannot
> write directly to the database and must pass through `hai`.

Negative prompt / exclusions:

> No doctors, stethoscopes, hospitals, pills, diagnosis imagery, cloud servers,
> surveillance cameras, multi-agent swarm, brain imagery, autonomous treatment
> language, dark dramatic lighting, or unreadable tiny text.

Expected output dimensions: 1600x900.
