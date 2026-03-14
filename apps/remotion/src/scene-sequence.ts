import { sceneSchema, type Scene } from "@manga/schema";

export type SequencedScene = Scene & {
  fromFrame: number;
  durationInFrames: number;
};

export function buildSceneSequence(
  scenes: unknown,
  options: { fps: number }
): SequencedScene[] {
  const parsedScenes = sceneSchema.array().parse(scenes);
  let fromFrame = 0;

  return parsedScenes.map((scene) => {
    const durationInFrames = Math.max(
      1,
      Math.ceil((scene.durationMs * options.fps) / 1000)
    );
    const sequencedScene = {
      ...scene,
      fromFrame,
      durationInFrames,
    };

    fromFrame += durationInFrames;
    return sequencedScene;
  });
}

export function getCompositionDurationInFrames(
  scenes: Array<{ fromFrame: number; durationInFrames: number }>
): number {
  return scenes.reduce(
    (total, scene) => Math.max(total, scene.fromFrame + scene.durationInFrames),
    0
  );
}
