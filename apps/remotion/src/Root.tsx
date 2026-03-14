import React from "react";

import { VideoComposition } from "./VideoComposition.tsx";

const h = React.createElement;

export function Root({ scenes, fps = 30 }) {
  return h(VideoComposition, { scenes, fps });
}
