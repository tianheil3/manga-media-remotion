import React from "react";

const h = React.createElement;

export function ImageMotion({ image, motion, stylePreset }) {
  return h(
    "figure",
    {
      className: "image-motion",
      "data-motion": motion,
      "data-style-preset": stylePreset,
    },
    h("img", {
      src: image,
      alt: image,
    })
  );
}
