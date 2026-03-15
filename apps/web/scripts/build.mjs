import { rebuildDist } from "./runtime-utils.mjs";

await rebuildDist({
  apiBaseUrl: process.env.MANGA_API_BASE_URL ?? process.env.VITE_API_BASE_URL ?? "",
});

console.log("Built apps/web review app to apps/web/dist");
