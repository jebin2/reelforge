import { ReelAnimation } from "./types";

export interface ClipBaseProps {
  zoomStart?: number;
  zoomEnd?: number;
  zoomSettleFraction?: number;
  panXStart?: number;
  panXEnd?: number;
  panYStart?: number;
  panYEnd?: number;
  shake?: boolean;
  fadeIn?: boolean;
  punchIn?: boolean;
  recoilEffect?: boolean;
  heartbeatEffect?: boolean;
  trembleEffect?: boolean;
  shockwaveEffect?: boolean;
  breatheEffect?: boolean;
  sfx?: string;
  sfxVolume?: number;
}

export function getAnimationProps(animation: ReelAnimation): ClipBaseProps {
  switch (animation) {

    // ── Impact / Energy ──────────────────────────────────────────────────────
    case "burst":
      return { zoomStart: 1.15, zoomEnd: 1.0, zoomSettleFraction: 0.25, shake: true, sfx: "sfx_impact.mp3", sfxVolume: 0.50 };
    case "snap":
      return { zoomStart: 1.2, zoomEnd: 1.0, zoomSettleFraction: 0.04, shake: true, sfx: "sfx_pop.mp3", sfxVolume: 0.55 };
    case "punch_in":
      return { punchIn: true, sfx: "sfx_slap.mp3", sfxVolume: 0.48 };
    case "recoil":
      return { recoilEffect: true, sfx: "sfx_boing.mp3", sfxVolume: 0.35 };
    case "shockwave":
      return { shockwaveEffect: true, sfx: "sfx_boxing.mp3", sfxVolume: 0.40 };

    // ── Tension / Sustained ──────────────────────────────────────────────────
    case "heartbeat":
      return { heartbeatEffect: true, sfx: "sfx_heartbeat.mp3", sfxVolume: 0.25 };
    case "tremble":
      return { trembleEffect: true, zoomStart: 1.0, zoomEnd: 1.02, sfx: "sfx_foliage.mp3", sfxVolume: 0.22 };
    case "breathe":
      return { breatheEffect: true, sfx: "sfx_breath.mp3", sfxVolume: 0.18 };

    // ── Camera ───────────────────────────────────────────────────────────────
    case "ken_burns":
      return { zoomStart: 1.0, zoomEnd: 1.08, panXStart: -10, panXEnd: 10 };
    case "zoom_out":
      return { zoomStart: 1.12, zoomEnd: 1.0, zoomSettleFraction: 0.5 };
    case "zoom_in":
      return { zoomStart: 1.0, zoomEnd: 1.12 };
    case "pan_up":
      return { zoomStart: 1.05, zoomEnd: 1.05, panYStart: 20, panYEnd: -20 };
    case "pan_down":
      return { zoomStart: 1.05, zoomEnd: 1.05, panYStart: -20, panYEnd: 20 };
    case "creep":
      return { zoomStart: 1.0, zoomEnd: 1.03 };
    case "fade_in":
      return { zoomStart: 1.0, zoomEnd: 1.04, fadeIn: true };

    default:
      return { zoomStart: 1.0, zoomEnd: 1.06 };
  }
}
