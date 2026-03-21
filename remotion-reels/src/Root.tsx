import React from "react";
import { AbsoluteFill, Composition } from "remotion";
import { ReelManifest } from "./types";
import { ReelSequences, getTotalFrames } from "./components/ReelSequences";

const defaultManifest: ReelManifest = {
  fps: 24,
  width: 1080,
  height: 1920,
  title: "Reel",
  clips: [
    {
      videoSrc: "",
      audioSrc: "",
      durationInSeconds: 5,
      animation: "ken_burns",
    },
  ],
};

const ReelVideoComp: React.FC<{ manifest: ReelManifest }> = ({ manifest }) => {
  return (
    <AbsoluteFill style={{ backgroundColor: "#000" }}>
      <ReelSequences manifest={manifest} />
    </AbsoluteFill>
  );
};

export const RemotionRoot: React.FC = () => {
  return (
    <Composition
      id="ReelVideo"
      component={ReelVideoComp}
      defaultProps={{ manifest: defaultManifest }}
      fps={defaultManifest.fps}
      width={defaultManifest.width}
      height={defaultManifest.height}
      durationInFrames={getTotalFrames(defaultManifest)}
      calculateMetadata={({ props }) => {
        const { manifest } = props;
        return {
          fps: manifest.fps,
          width: manifest.width,
          height: manifest.height,
          durationInFrames: getTotalFrames(manifest),
        };
      }}
    />
  );
};
