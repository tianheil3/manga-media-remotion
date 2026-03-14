import { sceneSchema, type Scene } from "@manga/schema";

type SubtitlePosition = "bottom-center" | "hidden";

export function buildSceneTemplateSpec(scene: unknown) {
  const parsedScene = sceneSchema.parse(scene);

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

function resolvedMotion(scene: Scene): Scene["cameraMotion"] | "pan" | "zoom-in" {
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

function subtitlePosition(scene: Scene): SubtitlePosition {
  return scene.type === "silent" ? "hidden" : "bottom-center";
}
