export function buildSceneTemplateSpec(scene) {
  const parsedScene = normalizeScene(scene);

  return {
    template: parsedScene.type,
    motion: resolvedMotion(parsedScene),
    subtitles: {
      visible: parsedScene.type !== "silent",
      text: parsedScene.type === "silent" ? undefined : parsedScene.subtitleText,
      position: subtitlePosition(parsedScene),
    },
  };
}

function resolvedMotion(scene) {
  if (scene.cameraMotion) {
    return scene.cameraMotion;
  }
  if (scene.type === "narration") {
    return "pan";
  }
  if (scene.type === "dialogue") {
    return "zoom-in";
  }
  return "none";
}

function subtitlePosition(scene) {
  return scene.type === "silent" ? "hidden" : "bottom-center";
}

function normalizeScene(scene) {
  if (!scene || typeof scene !== "object") {
    throw new TypeError("Scene must be an object.");
  }
  if (!scene.type) {
    throw new TypeError("Scene type is required.");
  }

  return scene;
}
