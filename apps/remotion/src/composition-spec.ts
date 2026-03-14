import type { Scene } from "@manga/schema";

import {
  buildSceneSequence,
  getCompositionDurationInFrames,
  type SequencedScene,
} from "./scene-sequence.ts";

export function buildCompositionSpec(
  scenes: unknown,
  options: { fps: number }
) {
  const sequencedScenes = buildSceneSequence(scenes, options);

  return {
    fps: options.fps,
    durationInFrames: getCompositionDurationInFrames(sequencedScenes),
    scenes: sequencedScenes.map(toRenderableScene),
  };
}

function toRenderableScene(scene: SequencedScene) {
  return {
    id: scene.id,
    template: scene.type,
    fromFrame: scene.fromFrame,
    durationInFrames: scene.durationInFrames,
    image: scene.image,
    subtitleText: subtitleText(scene),
    showSubtitles: scene.type !== "silent",
    audio: scene.audio,
    stylePreset: scene.stylePreset,
    transition: scene.transition,
  };
}

function subtitleText(scene: Scene): string | undefined {
  return scene.type === "silent" ? undefined : scene.subtitleText;
}
