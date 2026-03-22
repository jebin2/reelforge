# Task: Per-Clip Animation Assignment

## Goal
Assign the most visually appropriate animation and transition to each clip in a short-form reel video. The goal is a dynamic, varied video where consecutive clips feel distinct. Decisions are based purely on the narration text and word timings.

## Animation Types

### `burst`
**Use when:** Sudden violent moment — explosion, energy surge, physical impact.
**Effect:** Starts 1.15× zoomed, snaps to full size with camera shake.

### `punch_in`
**Use when:** Something rushes toward the viewer — a threat, a confrontation, a close-up demanding attention.
**Effect:** Aggressively zooms 1.0→1.2 in first 15%, then settles.

### `recoil`
**Use when:** A character is hit, knocked back, or surprised.
**Effect:** Quick zoom out to 0.9 then bounces back — like absorbing a blow.

### `shockwave`
**Use when:** Aftermath of explosion or impact — the ripple spreading outward.
**Effect:** Outward scale pulse in first 16 frames, then gentle drift.

### `heartbeat`
**Use when:** Tense standoff, waiting, suspense — something about to happen.
**Effect:** Rhythmic pulsing zoom (peaks every ~0.75s).

### `tremble`
**Use when:** Fear, instability, supernatural dread.
**Effect:** Rapid small shake fading out over first 40% of clip.

### `snap`
**Use when:** Single-frame impact moment — punch landing, bullet firing, lightning strike.
**Effect:** Ultra-fast zoom 1.2→1.0 in ~3 frames with shake.

### `ken_burns`
**Use when:** Calm, emotional, introspective moment or wide establishing shot. Good for dialogue.
**Effect:** Slow gentle zoom-in (1.0→1.08) with subtle horizontal drift.

### `zoom_in`
**Use when:** Building tension, approaching threat, ominous slow push.
**Effect:** Slow continuous push in (1.0→1.12) over full clip duration.

### `zoom_out`
**Use when:** Wide reveal — showing a location, crowd, or aftermath. Best for first clip.
**Effect:** Starts slightly zoomed (1.12×) and pulls back to full size.

### `pan_up`
**Use when:** Ascending action, hope, rising tension, revealing something above.
**Effect:** Camera drifts upward at a slight zoom.

### `pan_down`
**Use when:** Descending action, despair, falling, looking down at something.
**Effect:** Camera drifts downward at a slight zoom.

### `breathe`
**Use when:** Quiet reflective pause — aftermath, contemplation, grief.
**Effect:** One gentle zoom oscillation — the scene softly pulses.

### `creep`
**Use when:** Slow dread building — approaching danger, something wrong in a still scene.
**Effect:** Extremely slow push in (1.0→1.03). Almost imperceptible but unsettling.

### `fade_in`
**Use when:** New location, time jump, scene transition, or quiet moment needing breathing space.
**Effect:** Fades from black over first 30%, then gentle zoom drift.

## Rules
- **Vary the animations**: avoid assigning the same type to 3+ consecutive clips.
- First clip → `zoom_out` or `ken_burns`.
- `burst` should never appear on two consecutive clips.
- Action/combat narration → `burst`, `punch_in`, `snap`, or `recoil`.
- Dialogue/calm narration → `ken_burns`, `breathe`, or `zoom_in`.
- Suspense/tension narration → `heartbeat`, `creep`, or `tremble`.

## Transition Types

`transitionIn` controls how this clip enters from the previous one (always `none` for the first clip).

| Transition | Use when |
|---|---|
| `none` | Hard cut — after impact animations (`burst`, `snap`) |
| `fade` | Calm, emotional, or time-skip moments |
| `slide` | Sequential narrative flow |
| `wipe` | Scene change, location shift |
| `flip` | Dramatic reveal, plot twist |
| `toss` | High-energy transition, chaotic moment |

## Input Format
```json
{
  "show_name": "string",
  "clips": [
    {
      "clip_index": 0,
      "narration_text": "string",
      "duration_seconds": 3.5,
      "words": [
        {"word": "Frieza", "start": 0.10, "end": 0.35}
      ]
    }
  ]
}
```

## Output Format (JSON)
```json
{
  "clips": [
    {
      "clip_index": 0,
      "animation": "zoom_out",
      "transitionIn": "none",
      "reasoning": "one sentence"
    }
  ]
}
```

## Notes
- Return exactly one entry per clip, in order.
- `clip_index` must match the input order exactly.
- `transitionIn` is required in every entry — use `"none"` if not applicable.
- First clip must always have `transitionIn: "none"`.
- Use only these animation names: `burst`, `snap`, `punch_in`, `recoil`, `shockwave`, `heartbeat`, `tremble`, `ken_burns`, `zoom_out`, `zoom_in`, `pan_up`, `pan_down`, `breathe`, `creep`, `fade_in`.
- Use only these transition names: `none`, `fade`, `slide`, `wipe`, `flip`, `toss`.
