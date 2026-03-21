import React from "react";
import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";

interface Props {
  emoji: string;
}

export const EmojiOverlay: React.FC<Props> = ({ emoji }) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();

  // Bounce in with spring
  const bounceProgress = spring({
    frame,
    fps,
    config: { damping: 10, stiffness: 180, mass: 0.6 },
    durationInFrames: 20,
  });

  const scale = interpolate(bounceProgress, [0, 1], [0, 1]);

  // Pop pulse at peak (frame ~10–15)
  const popScale = frame > 8 && frame < 20
    ? interpolate(frame, [8, 12, 20], [1.0, 1.25, 1.0], { extrapolateRight: "clamp" })
    : 1.0;

  // Gentle float up over clip lifetime
  const floatY = interpolate(frame, [0, durationInFrames], [0, -30], { extrapolateRight: "clamp" });

  // Fade out near end
  const opacity = interpolate(
    frame,
    [0, 6, durationInFrames - 12, durationInFrames],
    [0, 1, 1, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );

  return (
    <AbsoluteFill
      style={{
        display: "flex",
        alignItems: "flex-start",
        justifyContent: "flex-end",
        paddingTop: "12%",
        paddingRight: "8%",
        pointerEvents: "none",
        zIndex: 50,
      }}
    >
      <div
        style={{
          fontSize: 96,
          lineHeight: 1,
          opacity,
          transform: `scale(${scale * popScale}) translateY(${floatY}px)`,
          transformOrigin: "center center",
          filter: "drop-shadow(0px 4px 12px rgba(0,0,0,0.6))",
          userSelect: "none",
        }}
      >
        {emoji}
      </div>
    </AbsoluteFill>
  );
};
