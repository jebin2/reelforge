import React from "react";
import {
  AbsoluteFill,
  Audio,
  Video,
  interpolate,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { ReelClip } from "../types";
import { ClipBaseProps } from "../animations";

interface Props extends ClipBaseProps {
  clip: ReelClip;
}

export const ClipBase: React.FC<Props> = ({
  clip,
  zoomStart = 1,
  zoomEnd = 1.06,
  zoomSettleFraction = 1,
  panXStart = 0,
  panXEnd = 0,
  panYStart = 0,
  panYEnd = 0,
  shake = false,
  fadeIn = false,
  punchIn = false,
  recoilEffect = false,
  heartbeatEffect = false,
  trembleEffect = false,
  shockwaveEffect = false,
  breatheEffect = false,
  sfx,
  sfxVolume = 0.35,
}) => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();
  const progress = frame / durationInFrames;

  // ── ZOOM ──────────────────────────────────────────────────────────────────
  let zoom = 1;

  if (punchIn) {
    const attackFrames = durationInFrames * 0.15;
    zoom = frame <= attackFrames
      ? interpolate(frame, [0, attackFrames], [1.0, 1.2], { extrapolateRight: "clamp" })
      : interpolate(frame, [attackFrames, durationInFrames], [1.2, 1.05], { extrapolateRight: "clamp" });
  } else if (recoilEffect) {
    zoom = interpolate(frame, [0, 6, 20, durationInFrames], [1.0, 0.9, 1.03, 1.01], { extrapolateRight: "clamp" });
  } else if (shockwaveEffect) {
    zoom = frame <= 16
      ? interpolate(frame, [0, 4, 16], [1.0, 1.06, 1.0], { extrapolateRight: "clamp" })
      : interpolate(frame, [16, durationInFrames], [1.0, 1.04], { extrapolateRight: "clamp" });
  } else if (heartbeatEffect) {
    const beatPeriod = 18;
    const phase = frame % beatPeriod;
    const beatZoom = phase < 4
      ? interpolate(phase, [0, 4], [1.0, 1.06], { extrapolateRight: "clamp" })
      : interpolate(phase, [4, beatPeriod], [1.06, 1.0], { extrapolateRight: "clamp" });
    zoom = beatZoom;
  } else if (breatheEffect) {
    zoom = 1.0 + 0.015 * Math.sin((frame / durationInFrames) * Math.PI * 2);
  } else {
    const settleFrame = durationInFrames * zoomSettleFraction;
    zoom = frame < settleFrame
      ? interpolate(frame, [0, settleFrame], [zoomStart, zoomEnd], { extrapolateRight: "clamp" })
      : zoomEnd;
  }

  // ── PAN ───────────────────────────────────────────────────────────────────
  const panX = interpolate(progress, [0, 1], [panXStart, panXEnd]);
  const panY = interpolate(progress, [0, 1], [panYStart, panYEnd]);

  // ── SHAKE ─────────────────────────────────────────────────────────────────
  let shakeX = 0;
  let shakeY = 0;
  if (shake || trembleEffect) {
    const intensity = shake
      ? interpolate(frame, [0, 8, durationInFrames], [12, 4, 0], { extrapolateRight: "clamp" })
      : interpolate(frame, [0, durationInFrames * 0.3, durationInFrames], [6, 3, 0], { extrapolateRight: "clamp" });
    shakeX = Math.sin(frame * 1.7) * intensity;
    shakeY = Math.cos(frame * 2.3) * intensity;
  }

  // ── FADE IN ───────────────────────────────────────────────────────────────
  const opacity = fadeIn
    ? interpolate(frame, [0, Math.min(18, durationInFrames * 0.25)], [0, 1], { extrapolateRight: "clamp" })
    : 1;

  const transform = `scale(${zoom}) translate(${panX + shakeX}px, ${panY + shakeY}px)`;

  return (
    <AbsoluteFill style={{ backgroundColor: "#000", overflow: "hidden", opacity }}>
      {/* Blurred background — fills black bars on sides for portrait video */}
      {clip.videoSrc && (
        <Video
          src={staticFile(clip.videoSrc)}
          style={{
            position: "absolute",
            width: "100%",
            height: "100%",
            objectFit: "cover",
            filter: "blur(28px) brightness(0.3)",
            transform: "scale(1.1)",
          }}
        />
      )}

      {/* Main video with animation */}
      {clip.videoSrc && (
        <Video
          src={staticFile(clip.videoSrc)}
          style={{
            position: "absolute",
            width: "100%",
            height: "100%",
            objectFit: "contain",
            transform,
            transformOrigin: "center center",
          }}
        />
      )}

      {sfx && <Audio src={staticFile(`sfx/${sfx}`)} volume={sfxVolume} />}
    </AbsoluteFill>
  );
};
