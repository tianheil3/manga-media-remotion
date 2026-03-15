import React from "react";
import { createRoot } from "react-dom/client";

import { ReviewApp } from "./browser/ReviewApp.tsx";

const container = document.getElementById("app");

if (!container) {
  throw new Error("Missing #app mount element.");
}

createRoot(container).render(
  React.createElement(ReviewApp, {
    env: globalThis.__MANGA_REVIEW_ENV__ ?? {},
    location: window.location,
    history: window.history,
  })
);
