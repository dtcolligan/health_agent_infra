# 3-minute screencast — shot list + script

This is the "what it looks like to install and use" demo for the top of
the README + the launch post. Target length **2:45–3:15**. Shorter is
better than longer; a skimmer decides in 20 seconds whether to keep
watching.

## Pre-flight (do once, before any take)

- [ ] Clean macOS or Linux box (VM or a fresh user account). The demo
      must start from "nothing installed."
- [ ] Terminal font 16pt+ so text is legible at 720p playback.
- [ ] Dark theme — the green "ok" / red "fail" coloring reads better.
- [ ] Wider-than-default terminal (120+ columns) so `hai stats` doesn't
      wrap.
- [ ] Valid intervals.icu athlete id + API key in a password manager, ready
      to paste. Garmin credentials are only needed if deliberately demoing the
      best-effort Garmin Connect path.
- [ ] Test `pipx` is installed (`brew install pipx` or distro equivalent)
      BEFORE starting the recording — we're demoing `hai`, not `pipx`.
- [ ] Have `~/.claude/skills/` empty (or renamed aside) so the skills
      copy step shows real output, not "already present."
- [ ] Shell history cleared; prompt short (`PS1='$ '`) so commands stand
      out.
- [ ] Monitor off sleep / notifications silenced / Do Not Disturb on.
- [ ] Recording tool: **asciinema** for the CLI-native feel (pastes as
      text, searchable, lightweight) OR OBS → YouTube if audio narration
      is wanted. Recommend asciinema for v1; add voiceover later only
      if it tests better.

## Shot list

The times below are **screen time** (elapsed in the recording). Typing
speed assumed normal; don't rush — legibility > brevity.

### Shot 1 · 0:00–0:15 · title card / install

```
$ pipx install health-agent-infra
```

Let pipx output scroll naturally. If it takes >10s, cut to the last
line ("installed package ...") in post.

**Voiceover (optional):** *"Health Agent Infra is a governed local
agent runtime for personal health data. One install, one CLI."*

### Shot 2 · 0:15–0:45 · setup + live-source auth

```
$ hai init
$ hai auth intervals-icu
```

The wizard should:
1. Scaffold config + state DB + skills (fast, 1–2s).
2. Prompt for intervals.icu athlete id + API key.
3. Store credentials in the OS keyring.
4. Leave the first pull to `hai daily`, where the source-resolution behavior
   is visible.

If step 4 takes >15s, **cut** in post to the last 2s of the progress
output. Don't let the viewer watch the network.

**Voiceover:** *"Setup scaffolds the state DB, copies skills into Claude
Code, and stores the live-source credential locally in the OS keyring.
Idempotent, safe to re-run."*

### Shot 3 · 0:45–0:55 · look at what landed

```
$ hai doctor
```

Show the green `ok` rows. Natural segue to "the state exists, it's
fresh, everything is ready for tomorrow."

**Voiceover:** *"`hai doctor` confirms config, DB, skills, credentials,
and per-source freshness. Green."*

### Shot 4 · 0:55–2:00 · the morning loop

```
$ hai daily
```

This is the centerpiece. Let the JSON report emit in full the first
time. Two sub-shots:

**4a (0:55–1:25)** — First run, no proposals yet. The output ends with
`"overall_status": "awaiting_proposals"`. Point out the skill invocation
seam: the runtime is asking Claude Code to post proposals.

**Voiceover:** *"The runtime pulled today, projected state, snapshotted
the cross-domain bundle, and paused at the agent seam. Skills are
judgment-only; code never improvises coaching prose."*

**4b (1:25–1:45)** — Switch to Claude Code. Show the agent invoking
domain skills, posting proposals via `hai propose`. *(If live agent use
makes the recording flaky, pre-run this step and cut to the "after"
state.)*

**4c (1:45–2:00)** — Re-run `hai daily`. Synthesis completes; plan and
recommendations get an atomic commit.

**Voiceover:** *"The agent emits per-domain proposals. Synthesis reconciles
them through codified cross-domain rules, and the runtime commits an
atomic plan."*

### Shot 5 · 2:00–2:20 · `hai explain`

```
$ hai explain --for-date $(date -u +%F) --user-id u_local_1 --operator
```

Show the audit-chain view: which proposals were made, which X-rules
fired, what changed, what the final recommendation was. This is the
"governed, not generative" proof.

**Voiceover:** *"Every rule firing is logged. `hai explain` reconstructs
the full chain from proposals through synthesis mutations to the final
recommendation."*

### Shot 6 · 2:20–2:40 · `hai stats`

```
$ hai stats
```

Sync freshness + recent runs + daily streak. Brief; proves ongoing
usage is observable locally.

**Voiceover:** *"No telemetry leaves the device. `hai stats` reads
local tables so you can see your own funnel without anyone else
reading it."*

### Shot 7 · 2:40–3:00 · closing frame

Static text overlay — no typing. Options:

- Repo URL (GitHub)
- Short license blurb ("MIT · local-only · no telemetry")
- "For Claude Code users on macOS / Linux"

End on the repo URL for ~3 seconds, then fade.

## Post-production

- **Trim ruthlessly.** Any frame where the viewer is watching the
  network/install is dead weight — cut.
- **Highlight the important lines** with a subtle flash or box
  annotation (asciinema → try [svg-term-cli](https://github.com/marionebl/svg-term-cli)
  for a cleaner render that plays anywhere).
- **Captions on by default.** Muted playback is the norm — the voiceover
  script above doubles as caption copy. If YouTube, upload `.srt`
  alongside.
- **Music: no.** Ambient music distracts from the command output and
  signals "promotional video." Keep it silent or voice-only.
- **Length floor: 2:45 · ceiling: 3:15.** If under 2:45 you skipped
  something; if over 3:15 you're losing the skimmer.

## Publishing

- **asciinema** (primary) — upload to asciinema.org, embed via `<script>`
  in the README. Pastes cleanly as text; works on HN / Reddit.
- **YouTube** (secondary) — only if a narrated version is recorded.
  Link alongside the asciinema from the README; don't substitute one
  for the other.
- **Don't auto-embed in the README** until the take is settled. A bad
  screencast is worse than no screencast. Hand-review once before
  merging.

## Framing decisions Dom owns

- **Voiceover or silent?** Voiceover doubles reach on social platforms
  but requires a retake if his voice sounds rushed. Silent is easier
  to iterate.
- **Live agent or pre-staged?** Live shows authenticity; pre-staged
  shows the happy path reliably. My recommendation: pre-stage the
  agent interaction so the demo doesn't depend on Anthropic API
  latency, but show the `hai propose` commits landing in real time.
- **Include `hai review record`?** Closes the loop on "did the plan
  work?" but adds 30s. Skip for v1 — add in a sequel video if the
  first one lands.
