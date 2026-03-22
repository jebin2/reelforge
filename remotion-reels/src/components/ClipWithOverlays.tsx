import React from "react";
import { AbsoluteFill } from "remotion";
import { KineticSubtitles, getAnimationProps } from "remotion-animation-kit";
import { ReelClip } from "../types";
import { ClipBase } from "./ClipBase";
import { EmojiOverlay } from "./EmojiOverlay";

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
        <KineticSubtitles wordTimings={clip.wordTimings} />
      )}
    </AbsoluteFill>
  );
};
