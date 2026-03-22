import type { AnimationName, TransitionName, WordTiming } from "remotion-animation-kit";

export interface ReelClip {
  videoSrc: string;
  audioSrc: string;
  durationInSeconds: number;
  emojiText?: string;
  wordTimings?: WordTiming[];
  animation: AnimationName;
  transitionIn?: TransitionName;
}

export interface ReelManifest {
  fps: number;
  width: number;
  height: number;
  title: string;
  clips: ReelClip[];
}
