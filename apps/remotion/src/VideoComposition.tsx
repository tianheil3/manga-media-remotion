import React from "react";

import { buildCompositionSpec } from "./composition-spec.ts";
import { buildSceneTemplateSpec } from "./scene-template-spec.ts";
import { DialogueScene } from "./components/scenes/DialogueScene.tsx";
import { NarrationScene } from "./components/scenes/NarrationScene.tsx";
import { SilentScene } from "./components/scenes/SilentScene.tsx";

const h = React.createElement;

export function VideoComposition({ scenes, fps = 30 }) {
  const composition = buildCompositionSpec(scenes, { fps });

  return h(
    "section",
    {
      className: "video-composition",
      "data-fps": String(composition.fps),
      "data-duration-in-frames": String(composition.durationInFrames),
    },
    ...composition.scenes.map((scene) => {
      const template = buildSceneTemplateSpec(
        scenes.find((entry) => entry.id === scene.id)
      );
      const sceneProps = {
        ...scene,
        motion: template.motion,
      };

      if (scene.template === "narration") {
        return h(NarrationScene, { key: scene.id, scene: sceneProps });
      }

      if (scene.template === "dialogue") {
        return h(DialogueScene, { key: scene.id, scene: sceneProps });
      }

      return h(SilentScene, { key: scene.id, scene: sceneProps });
    })
  );
}
