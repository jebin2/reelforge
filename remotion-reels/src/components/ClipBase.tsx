import React from "react";
import { Img, OffthreadVideo, staticFile } from "remotion";
import { AnimatedBase } from "remotion-animation-kit";
import type { BaseAnimationProps } from "remotion-animation-kit";
import { ReelClip } from "../types";

interface Props extends BaseAnimationProps {
  clip: ReelClip;
}

export const ClipBase: React.FC<Props> = ({ clip, ...animProps }) => {
  const mediaSrc = clip.videoSrc || clip.imageSrc;
  const isImage = !clip.videoSrc && !!clip.imageSrc;

  const background = mediaSrc ? (
    isImage ? (
      <Img
        src={staticFile(mediaSrc)}
        style={{
          position: "absolute",
          width: "100%",
          height: "100%",
          objectFit: "cover",
          filter: "blur(28px) brightness(0.3)",
          transform: "scale(1.1)",
        }}
      />
    ) : (
      <OffthreadVideo
        src={staticFile(mediaSrc)}
        style={{
          position: "absolute",
          width: "100%",
          height: "100%",
          objectFit: "cover",
          filter: "blur(28px) brightness(0.3)",
          transform: "scale(1.1)",
        }}
      />
    )
  ) : undefined;

  return (
    <AnimatedBase {...animProps} background={background} audioSrc={clip.audioSrc}>
      {mediaSrc && (
        isImage ? (
          <Img
            src={staticFile(mediaSrc)}
            style={{ width: "100%", height: "100%", objectFit: "contain" }}
          />
        ) : (
          <OffthreadVideo
            src={staticFile(mediaSrc)}
            style={{ width: "100%", height: "100%", objectFit: "contain" }}
          />
        )
      )}
    </AnimatedBase>
  );
};
