import { mkdir, readdir, readFile, writeFile, copyFile, rm } from "node:fs/promises";
import { dirname, extname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

export const webRoot = fileURLToPath(new URL("../", import.meta.url));
export const repoRoot = fileURLToPath(new URL("../../../", import.meta.url));
export const webSrcRoot = join(webRoot, "src");
export const remotionSrcRoot = join(repoRoot, "apps/remotion/src");
export const distRoot = join(webRoot, "dist");

export async function renderIndexHtml({ entryScript, stylesheetHref, apiBaseUrl }) {
  const template = await readFile(join(webRoot, "index.html"), "utf8");

  return template
    .replaceAll("__ENTRY_SCRIPT__", entryScript)
    .replaceAll("__STYLESHEET_HREF__", stylesheetHref)
    .replaceAll(
      "__MANGA_ENV_JSON__",
      JSON.stringify({
        MANGA_API_BASE_URL: apiBaseUrl,
        VITE_API_BASE_URL: apiBaseUrl,
      })
    );
}

export async function rebuildDist({ apiBaseUrl = "" } = {}) {
  await rm(distRoot, { recursive: true, force: true });
  await copyRuntimeTree(webSrcRoot, join(distRoot, "src"));
  await copyRuntimeTree(remotionSrcRoot, join(distRoot, "remotion/src"));

  const indexHtml = await renderIndexHtml({
    entryScript: "./src/main.js",
    stylesheetHref: "./src/browser/review-app.css",
    apiBaseUrl,
  });
  await writeFile(join(distRoot, "index.html"), indexHtml, "utf8");
}

export function toJsModuleSource(source) {
  return source
    .replace(/(from\s+["'][^"']+)\.(ts|tsx)(["'])/g, "$1.js$3")
    .replace(/(import\s*\(\s*["'][^"']+)\.(ts|tsx)(["']\s*\))/g, "$1.js$3");
}

export async function readRuntimeFile(pathname) {
  if (pathname === "/" || pathname === "/index.html") {
    return {
      contentType: "text/html; charset=utf-8",
      body: await renderIndexHtml({
        entryScript: "/src/main.tsx",
        stylesheetHref: "/src/browser/review-app.css",
        apiBaseUrl: process.env.MANGA_API_BASE_URL ?? process.env.VITE_API_BASE_URL ?? "",
      }),
    };
  }

  const filePath = resolveRuntimePath(pathname);
  const source = await readFile(filePath);
  const extension = extname(filePath);

  if (extension === ".ts" || extension === ".tsx") {
    return {
      contentType: "text/javascript; charset=utf-8",
      body: source,
    };
  }

  if (extension === ".css") {
    return {
      contentType: "text/css; charset=utf-8",
      body: source,
    };
  }

  return {
    contentType: "application/octet-stream",
    body: source,
  };
}

function resolveRuntimePath(pathname) {
  if (pathname.startsWith("/src/")) {
    return resolve(webRoot, pathname.slice(1));
  }

  if (pathname.startsWith("/remotion/src/")) {
    return resolve(repoRoot, `apps/${pathname.slice(1)}`);
  }

  throw new Error(`Unsupported runtime path: ${pathname}`);
}

async function copyRuntimeTree(sourceDir, targetDir) {
  await mkdir(targetDir, { recursive: true });
  const entries = await readdir(sourceDir, { withFileTypes: true });

  for (const entry of entries) {
    const sourcePath = join(sourceDir, entry.name);
    const targetPath =
      entry.isFile() && (entry.name.endsWith(".ts") || entry.name.endsWith(".tsx"))
        ? join(targetDir, replaceModuleExtension(entry.name))
        : join(targetDir, entry.name);

    if (entry.isDirectory()) {
      await copyRuntimeTree(sourcePath, targetPath);
      continue;
    }

    await mkdir(dirname(targetPath), { recursive: true });

    if (entry.name.endsWith(".ts") || entry.name.endsWith(".tsx")) {
      const source = await readFile(sourcePath, "utf8");
      await writeFile(targetPath, toJsModuleSource(source), "utf8");
      continue;
    }

    await copyFile(sourcePath, targetPath);
  }
}

function replaceModuleExtension(filename) {
  return filename.replace(/\.(ts|tsx)$/u, ".js");
}
