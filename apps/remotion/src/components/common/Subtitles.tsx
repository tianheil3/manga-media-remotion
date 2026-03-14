import React from "react";

const h = React.createElement;

export function Subtitles({ text, visible }) {
  if (!visible || !text) {
    return null;
  }

  return h(
    "p",
    {
      className: "subtitles",
      "data-subtitles-visible": "true",
    },
    text
  );
}
