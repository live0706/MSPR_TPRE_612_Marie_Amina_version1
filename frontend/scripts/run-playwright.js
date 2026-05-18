import { spawn } from "node:child_process";
import { createServer } from "node:http";
import { readFile } from "node:fs/promises";
import { existsSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const HOST = "127.0.0.1";
const PORT = 4173;
const BASE_URL = `http://${HOST}:${PORT}/`;
const TARGET_BASE_URL = process.env.PLAYWRIGHT_BASE_URL || BASE_URL;
const PLAYWRIGHT_ARGS = ["playwright", "test", ...process.argv.slice(2)];
const NPX_COMMAND = process.platform === "win32" ? "npx.cmd" : "npx";
const MIME_TYPES = {
  ".css": "text/css; charset=utf-8",
  ".html": "text/html; charset=utf-8",
  ".js": "application/javascript; charset=utf-8",
  ".json": "application/json; charset=utf-8",
  ".png": "image/png",
  ".svg": "image/svg+xml; charset=utf-8"
};

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const DIST_DIR = path.resolve(__dirname, "..", "dist");

async function isServerAlreadyRunning(url) {
  try {
    const response = await fetch(url);
    return response.ok;
  } catch {
    return false;
  }
}

function getContentType(filePath) {
  return MIME_TYPES[path.extname(filePath)] || "application/octet-stream";
}

function createStaticServer() {
  return createServer(async (request, response) => {
    try {
      const url = new URL(request.url || "/", BASE_URL);
      const cleanPath = url.pathname === "/" ? "/index.html" : url.pathname;
      const requestedFile = path.resolve(DIST_DIR, `.${cleanPath}`);
      const safeFile =
        requestedFile.startsWith(DIST_DIR) && existsSync(requestedFile)
          ? requestedFile
          : path.join(DIST_DIR, "index.html");

      const body = await readFile(safeFile);
      response.writeHead(200, { "Content-Type": getContentType(safeFile) });
      response.end(body);
    } catch (error) {
      response.writeHead(500, { "Content-Type": "text/plain; charset=utf-8" });
      response.end(error instanceof Error ? error.message : "Erreur serveur");
    }
  });
}

function startStaticServer() {
  return new Promise((resolve, reject) => {
    const server = createStaticServer();
    server.once("error", reject);
    server.listen(PORT, HOST, () => resolve(server));
  });
}

function spawnCommand(command, args, options = {}) {
  if (process.platform === "win32") {
    return spawn("cmd.exe", ["/c", command, ...args], {
      ...options,
      shell: false
    });
  }

  return spawn(command, args, {
    ...options,
    shell: false
  });
}

async function run() {
  let server = null;
  let ownsServer = false;

  try {
    const useEmbeddedStaticServer = TARGET_BASE_URL === BASE_URL;

    if (useEmbeddedStaticServer && !existsSync(path.join(DIST_DIR, "index.html"))) {
      throw new Error("Le build frontend est absent. Lance d'abord `npm run build`.");
    }

    if (useEmbeddedStaticServer && !(await isServerAlreadyRunning(BASE_URL))) {
      server = await startStaticServer();
      ownsServer = true;
    }

    const exitCode = await new Promise((resolve, reject) => {
      const runner = spawnCommand(NPX_COMMAND, PLAYWRIGHT_ARGS, {
        stdio: "inherit"
      });

      runner.once("exit", (code) => resolve(code ?? 1));
      runner.once("error", reject);
    });

    process.exitCode = exitCode;
  } catch (error) {
    console.error(error instanceof Error ? error.message : error);
    process.exitCode = 1;
  } finally {
    if (ownsServer && server) {
      await new Promise((resolve) => server.close(() => resolve()));
    }
  }
}

run();
