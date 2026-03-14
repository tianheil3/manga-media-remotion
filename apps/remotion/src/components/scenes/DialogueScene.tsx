import React from "react";

import { ImageMotion } from "../common/ImageMotion.tsx";
import { Subtitles } from "../common/Subtitles.tsx";

const h = React.createElement;

export function DialogueScene({ scene }) {
  return h(
    "article",
    {
      className: "scene dialogue-scene",
      "data-scene-id": scene.id,
      "data-scene-type": "dialogue",
      "data-duration-in-frames": String(scene.durationInFrames),
      "data-audio": scene.audio ?? "",
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
