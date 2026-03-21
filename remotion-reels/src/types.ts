export type ReelAnimation =
  // Camera
  | "ken_burns"    // slow zoom + horizontal drift
  | "zoom_in"      // slow push in 1.0→1.12
  | "zoom_out"     // zoom out 1.12→1.0
  | "pan_up"       // camera drifts upward
  | "pan_down"     // camera drifts downward
  // Impact
  | "burst"        // zoom burst fast
  | "snap"         // ultra-fast zoom — instant hit
  | "punch_in"     // aggressive zoom 1.0→1.2 fast, settle
  | "recoil"       // quick zoom out then bounce back
  | "shockwave"    // outward pulse
  // Tension
  | "heartbeat"    // rhythmic pulsing zoom
  | "tremble"      // rapid small shake
  | "breathe"      // gentle oscillating zoom
  | "creep"        // extremely slow zoom — dread
  | "fade_in";     // fade from black

export type ReelTransition = "none" | "fade" | "slide" | "wipe" | "flip" | "toss";

export interface WordTiming {
  word: string;
  start: number;
  end: number;
}

export interface ReelClip {
  videoSrc: string;           // path to auto_crop_9x16 video clip (under public/)
  audioSrc: string;           // path to TTS audio wav (under public/)
  durationInSeconds: number;
  emojiText?: string;         // emoji character to animate over clip e.g. "🔥"
  wordTimings?: WordTiming[]; // for kinetic subtitles
  animation: ReelAnimation;
  transitionIn?: ReelTransition;
}

export interface ReelManifest {
  fps: number;
  width: number;              // 1080 for portrait shorts
  height: number;             // 1920 for portrait shorts
  title: string;              // shown on animated title card
  clips: ReelClip[];
}
