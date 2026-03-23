import React from "react";
import { OffthreadVideo, staticFile } from "remotion";
import { AnimatedBase } from "remotion-animation-kit";
import type { BaseAnimationProps } from "remotion-animation-kit";
import { ReelClip } from "../types";

interface Props extends BaseAnimationProps {
  clip: ReelClip;
}

export const ClipBase: React.FC<Props> = ({ clip, ...animProps }) => {
  const background = clip.videoSrc ? (
    <OffthreadVideo
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
  ) : undefined;

  return (
    <AnimatedBase {...animProps} background={background} audioSrc={clip.audioSrc}>
      {clip.videoSrc && (
        <OffthreadVideo
          src={staticFile(clip.videoSrc)}
          style={{ width: "100%", height: "100%", objectFit: "contain" }}
        />
      )}
    </AnimatedBase>
  );
};
