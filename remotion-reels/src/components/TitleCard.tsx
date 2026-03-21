import React from "react";
import { AbsoluteFill, interpolate, spring, staticFile, useCurrentFrame, useVideoConfig } from "remotion";

interface Props {
  title: string;
}

export const TitleCard: React.FC<Props> = ({ title }) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();

  // Background pulse — subtle radial glow
  const glowOpacity = interpolate(
    frame,
    [0, 20, durationInFrames - 10, durationInFrames],
    [0, 0.7, 0.7, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );

  // Title punches in with spring
  const titleSpring = spring({ frame, fps, config: { damping: 14, stiffness: 120 }, durationInFrames: 30 });
  const titleScale = interpolate(titleSpring, [0, 1], [0.5, 1]);
  const titleOpacity = interpolate(frame, [0, 12], [0, 1], { extrapolateRight: "clamp" });

  // Subtitle slides up from below
  const subtitleY = interpolate(
    frame,
    [10, 30],
    [40, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );
  const subtitleOpacity = interpolate(frame, [10, 28], [0, 1], { extrapolateRight: "clamp" });

  // Whole card fades out at end
  const cardOpacity = interpolate(
    frame,
    [durationInFrames - 15, durationInFrames],
    [1, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );

  return (
    <AbsoluteFill
      style={{
        backgroundColor: "#0a0a0a",
        opacity: cardOpacity,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        overflow: "hidden",
      }}
    >
      <style>{`
        @font-face {
          font-family: 'Bungee';
          src: url('${staticFile("fonts/Bungee-Regular.ttf")}');
        }
      `}</style>

      {/* Radial glow behind title */}
      <div
        style={{
          position: "absolute",
          width: 700,
          height: 700,
          borderRadius: "50%",
          background: "radial-gradient(circle, rgba(255,60,60,0.35) 0%, transparent 70%)",
          opacity: glowOpacity,
        }}
      />

      {/* "RECAP" label */}
      <div
        style={{
          opacity: subtitleOpacity,
          transform: `translateY(${subtitleY}px)`,
          fontFamily: "Bungee, sans-serif",
          fontSize: 36,
          color: "#ff3c3c",
          letterSpacing: 12,
          textTransform: "uppercase",
          marginBottom: 24,
        }}
      >
        RECAP
      </div>

      {/* Main title */}
      <div
        style={{
          opacity: titleOpacity,
          transform: `scale(${titleScale})`,
          transformOrigin: "center center",
          fontFamily: "Bungee, sans-serif",
          fontSize: title.length > 20 ? 72 : 96,
          fontWeight: 900,
          color: "#ffffff",
          textTransform: "uppercase",
          textAlign: "center",
          lineHeight: 1.1,
          paddingLeft: 60,
          paddingRight: 60,
          filter: "drop-shadow(0px 6px 24px rgba(255,60,60,0.5))",
          wordBreak: "break-word",
        }}
      >
        {title}
      </div>

      {/* Bottom accent line */}
      <div
        style={{
          marginTop: 40,
          opacity: subtitleOpacity,
          width: interpolate(frame, [20, 40], [0, 280], { extrapolateRight: "clamp" }),
          height: 4,
          background: "linear-gradient(90deg, transparent, #ff3c3c, transparent)",
          borderRadius: 2,
        }}
      />
    </AbsoluteFill>
  );
};
