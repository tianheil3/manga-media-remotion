export function buildSceneSequence(
  scenes,
  options
) {
  if (!Array.isArray(scenes)) {
    throw new TypeError("Scenes must be an array.");
  }

  const parsedScenes = scenes.map(normalizeScene);
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
  scenes
) {
  return scenes.reduce(
    (total, scene) => Math.max(total, scene.fromFrame + scene.durationInFrames),
    0
  );
}

function normalizeScene(scene) {
  if (!scene || typeof scene !== "object") {
    throw new TypeError("Scene entries must be objects.");
  }
  if (!scene.id) {
    throw new TypeError("Scene entries must include id.");
  }
  if (scene.durationMs === undefined || scene.durationMs === null || Number.isNaN(Number(scene.durationMs))) {
    throw new TypeError("Scene entries must include durationMs.");
  }
  if (!scene.type) {
    throw new TypeError("Scene entries must include type.");
  }
  if (!scene.image) {
    throw new TypeError("Scene entries must include image.");
  }

  return {
    ...scene,
    durationMs: Number(scene.durationMs),
  };
}
