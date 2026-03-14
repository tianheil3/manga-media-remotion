import test from "node:test";
import assert from "node:assert/strict";

import React from "react";
import { renderToStaticMarkup } from "react-dom/server";

import { Root } from "../src/Root.tsx";

test("root composition renders narration dialogue and silent scenes with scene durations", () => {
  const markup = renderToStaticMarkup(
    React.createElement(Root, {
      fps: 30,
      scenes: [
        {
          id: "scene-001",
          type: "narration",
          image: "images/001.png",
          subtitleText: "Narration subtitle",
          durationMs: 1000,
          stylePreset: "default",
        },
        {
          id: "scene-002",
          type: "dialogue",
          image: "images/002.png",
          subtitleText: "Dialogue subtitle",
          audio: "audio/002.wav",
          durationMs: 1200,
          stylePreset: "dramatic",
        },
        {
          id: "scene-003",
          type: "silent",
          image: "images/003.png",
          durationMs: 800,
          stylePreset: "calm",
        },
      ],
    })
  );

  assert.match(markup, /data-scene-type="narration"/);
  assert.match(markup, /data-scene-type="dialogue"/);
  assert.match(markup, /data-scene-type="silent"/);
  assert.match(markup, /data-duration-in-frames="30"/);
  assert.match(markup, /data-duration-in-frames="36"/);
  assert.match(markup, /data-duration-in-frames="24"/);
  assert.match(markup, /Narration subtitle/);
  assert.match(markup, /Dialogue subtitle/);
  assert.doesNotMatch(markup, /scene-003[\s\S]*subtitle/i);
});
