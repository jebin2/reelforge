import React from "react";
import { AbsoluteFill, Sequence } from "remotion";
import { TransitionSeries, springTiming } from "@remotion/transitions";
import { ReelManifest } from "../types";
import { ClipWithOverlays } from "./ClipWithOverlays";
import { getPresentation, TRANSITION_FRAMES, TitleCard, getTitleCardDuration } from "remotion-animation-kit";

const TITLE_CARD_FRAMES = getTitleCardDuration(24);

export function getTotalFrames(manifest: ReelManifest): number {
  const clipFrames = manifest.clips.reduce((sum, clip, i) => {
    const frames = Math.ceil(clip.durationInSeconds * manifest.fps);
    const hasTransition = i > 0 && clip.transitionIn && clip.transitionIn !== "none";
    return sum + frames - (hasTransition ? TRANSITION_FRAMES : 0);
  }, 0);
  return TITLE_CARD_FRAMES + clipFrames;
}

interface Props {
  manifest: ReelManifest;
}

export const ReelSequences: React.FC<Props> = ({ manifest }) => {
  const { fps, clips, title } = manifest;
  return (
    <AbsoluteFill>
      <Sequence from={0} durationInFrames={TITLE_CARD_FRAMES} layout="none">
        <TitleCard title={title} media={clips.map((c) => ({ videoSrc: c.videoSrc }))} />
      </Sequence>

      <Sequence from={TITLE_CARD_FRAMES} layout="none">
        <TransitionSeries>
          {clips.map((clip, i) => {
            const durationInFrames = Math.ceil(clip.durationInSeconds * fps);
            const transition = i === 0 ? "none" : (clip.transitionIn ?? "fade");

            return (
              <React.Fragment key={i}>
                {transition !== "none" && (
                  <TransitionSeries.Transition
                    presentation={getPresentation(transition)}
                    timing={springTiming({ durationInFrames: TRANSITION_FRAMES })}
                  />
                )}
                <TransitionSeries.Sequence durationInFrames={durationInFrames}>
                  <ClipWithOverlays clip={clip} fps={fps} />
                </TransitionSeries.Sequence>
              </React.Fragment>
            );
          })}
        </TransitionSeries>
      </Sequence>
    </AbsoluteFill>
  );
};
