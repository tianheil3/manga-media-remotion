import { createServer } from "node:http";

import { readRuntimeFile } from "./runtime-utils.mjs";

const { host, port } = parseArgs(process.argv.slice(2));

const server = createServer(async (request, response) => {
  try {
    const url = new URL(request.url ?? "/", `http://${request.headers.host ?? `${host}:${port}`}`);
    const payload = await readRuntimeFile(url.pathname);
    response.writeHead(200, { "content-type": payload.contentType });
    response.end(payload.body);
  } catch (error) {
    response.writeHead(error?.code === "ENOENT" ? 404 : 500, {
      "content-type": "text/plain; charset=utf-8",
    });
    response.end(error instanceof Error ? error.message : String(error));
  }
});

server.listen(port, host, () => {
  console.log(`apps/web dev server running at http://${host}:${port}`);
});

function parseArgs(argv) {
  const options = {
    host: "127.0.0.1",
    port: 4173,
  };

  for (let index = 0; index < argv.length; index += 1) {
    const value = argv[index];
    if (value === "--host" && argv[index + 1]) {
      options.host = argv[index + 1];
      index += 1;
      continue;
    }
    if (value === "--port" && argv[index + 1]) {
      options.port = Number.parseInt(argv[index + 1], 10);
      index += 1;
    }
  }

  return options;
}
