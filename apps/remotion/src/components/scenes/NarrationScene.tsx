import React from "react";

import { ImageMotion } from "../common/ImageMotion.tsx";
import { Subtitles } from "../common/Subtitles.tsx";

const h = React.createElement;

export function NarrationScene({ scene }) {
  return h(
    "article",
    {
      className: "scene narration-scene",
      "data-scene-id": scene.id,
      "data-scene-type": "narration",
      "data-duration-in-frames": String(scene.durationInFrames),
    },
    h(ImageMotion, {
      image: scene.image,
      motion: scene.motion,
      stylePreset: scene.stylePreset,
    }),
    h(Subtitles, {
      visible: true,
      text: scene.subtitleText,
    })
  );
}
