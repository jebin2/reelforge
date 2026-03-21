import React from "react";
import { AbsoluteFill } from "remotion";
import { ReelClip } from "../types";
import { ClipBase } from "./ClipBase";
import { KineticSubtitles } from "./KineticSubtitles";
import { EmojiOverlay } from "./EmojiOverlay";
import { getAnimationProps } from "../animations";

// Adapt KineticSubtitles which expects PanelData — we pass a compatible shape
function adaptClip(clip: ReelClip) {
  return {
    imageSrc: "",
    audioSrc: clip.audioSrc,
    durationInSeconds: clip.durationInSeconds,
    bubbleBbox: [0, 0, 1080, 1920] as [number, number, number, number],
    narrationText: "",
    sceneCaption: "",
    animation: "ken_burns" as const,
    wordTimings: clip.wordTimings,
  };
}

interface Props {
  clip: ReelClip;
  fps: number;
}

export const ClipWithOverlays: React.FC<Props> = ({ clip }) => {
  const animProps = getAnimationProps(clip.animation);

  return (
    <AbsoluteFill>
      <ClipBase clip={clip} {...animProps} />

      {clip.emojiText && <EmojiOverlay emoji={clip.emojiText} />}

      {clip.wordTimings && clip.wordTimings.length > 0 && (
        <KineticSubtitles panel={adaptClip(clip) as any} />
      )}
    </AbsoluteFill>
  );
};
