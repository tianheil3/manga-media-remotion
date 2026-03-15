import { readFile } from "node:fs/promises";

const SHIM_SPECIFIERS = new Map([
  ["@manga/schema", new URL("../packages/schema/src/index.ts", import.meta.url)],
  ["react", new URL("./shims/react.mjs", import.meta.url)],
  ["react-dom/server", new URL("./shims/react-dom-server.mjs", import.meta.url)],
  ["zod", new URL("./shims/zod.mjs", import.meta.url)],
]);

export async function resolve(specifier, context, nextResolve) {
  const shimUrl = SHIM_SPECIFIERS.get(specifier);
  try {
    return await nextResolve(specifier, context);
  } catch (error) {
    if (!shimUrl || error?.code !== "ERR_MODULE_NOT_FOUND") {
      throw error;
    }

    return {
      shortCircuit: true,
      url: shimUrl.href,
    };
  }
}
export async function load(url, context, nextLoad) {
  if (url.endsWith(".tsx")) {
    return {
      format: "module",
      shortCircuit: true,
      source: await readFile(new URL(url), "utf8"),
    };
  }

  return nextLoad(url, context);
}
