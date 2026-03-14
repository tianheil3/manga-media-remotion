import React from "react";

import { ImageMotion } from "../common/ImageMotion.tsx";

const h = React.createElement;

export function SilentScene({ scene }) {
  return h(
    "article",
    {
      className: "scene silent-scene",
      "data-scene-id": scene.id,
      "data-scene-type": "silent",
      "data-duration-in-frames": String(scene.durationInFrames),
    },
    h(ImageMotion, {
      image: scene.image,
      motion: scene.motion,
      stylePreset: scene.stylePreset,
    })
  );
}
