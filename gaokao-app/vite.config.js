import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import fs from "node:fs";
import path from "node:path";

const PAPERS_ROOT = path.resolve(__dirname, "../gaokao-papers");

function createStaticMountMiddleware() {
  const mimeTypes = {
    ".json": "application/json; charset=utf-8",
    ".txt": "text/plain; charset=utf-8",
    ".md": "text/markdown; charset=utf-8",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".gif": "image/gif",
    ".webp": "image/webp",
    ".svg": "image/svg+xml; charset=utf-8",
    ".pdf": "application/pdf",
  };

  return (req, res, next) => {
    const rawUrl = (req.url || "").split("?")[0];
    let mountPrefix = null;
    if (rawUrl.startsWith("/bank/")) {
      mountPrefix = "/bank/";
    } else if (rawUrl.startsWith("/collected/")) {
      mountPrefix = "/collected/";
    }
    if (!mountPrefix) {
      return next();
    }

    let relDecoded;
    try {
      relDecoded = decodeURIComponent(rawUrl.slice(1));
    } catch {
      res.statusCode = 400;
      res.end("Bad URL encoding");
      return;
    }

    const absPath = path.resolve(PAPERS_ROOT, relDecoded);
    if (!absPath.startsWith(PAPERS_ROOT + path.sep)) {
      res.statusCode = 403;
      res.end("Forbidden");
      return;
    }

    fs.stat(absPath, (err, stat) => {
      if (err || !stat.isFile()) {
        res.statusCode = 404;
        res.end("Not found");
        return;
      }
      const ext = path.extname(absPath).toLowerCase();
      res.setHeader("Content-Type", mimeTypes[ext] || "application/octet-stream");
      res.setHeader("Cache-Control", ext === ".json" ? "no-cache" : "public, max-age=3600");
      fs.createReadStream(absPath).pipe(res);
    });
  };
}

export default defineConfig({
  base: process.env.VITE_APP_BASE || "/",
  plugins: [
    react(),
    {
      name: "serve-gaokao-papers",
      configureServer(server) {
        server.middlewares.use(createStaticMountMiddleware());
      },
      configurePreviewServer(server) {
        server.middlewares.use(createStaticMountMiddleware());
      },
      closeBundle() {
        const srcBank = path.join(PAPERS_ROOT, "bank");
        const dstBank = path.resolve(__dirname, "dist", "bank");
        if (fs.existsSync(srcBank)) {
          fs.cpSync(srcBank, dstBank, { recursive: true, force: true });
        }
      },
    },
  ],
});
