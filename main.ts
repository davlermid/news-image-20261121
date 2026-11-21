// Entry program for news-image-20261121 (Node 22, standard library only).
// generate.py draws the poster and ships it in this repo as entry.png;
// this program places that file at the grader's output path and checks
// that what landed there is a complete PNG of the expected size.
//
// Local check: mkdir -p out && MAKEFUN_OUTPUT_DIR=out node main.ts

import { copyFileSync, existsSync, mkdirSync, readFileSync, statSync } from "node:fs";
import { join } from "node:path";

const outDir = process.env.MAKEFUN_OUTPUT_DIR ?? "/output";
mkdirSync(outDir, { recursive: true });

const source = new URL("./entry.png", import.meta.url);
if (!existsSync(source)) {
  throw new Error(
    `entry.png is missing next to main.ts (${source.pathname}); run generate.py to draw it first.`,
  );
}

const sourceBytes = statSync(source).size;
if (sourceBytes === 0) {
  throw new Error("entry.png is empty (0 bytes); refusing to submit a blank image.");
}
if (sourceBytes > 1048576) {
  throw new Error(`entry.png is ${sourceBytes} bytes, over the 1 MiB limit.`);
}

const dest = join(outDir, "entry.png");
copyFileSync(source, dest);

const copiedBytes = statSync(dest).size;
if (copiedBytes !== sourceBytes) {
  throw new Error(
    `output entry.png has ${copiedBytes} bytes but the source has ${sourceBytes}; the copy is incomplete.`,
  );
}

// A whole PNG starts with this 8-byte signature and ends with the IEND chunk.
const bytes = readFileSync(dest);
const pngSignature = Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]);
if (!bytes.subarray(0, 8).equals(pngSignature)) {
  throw new Error("output entry.png does not start with the PNG signature.");
}
const iendType = bytes.subarray(bytes.length - 8, bytes.length - 4).toString("ascii");
if (iendType !== "IEND") {
  throw new Error("output entry.png does not end with an IEND chunk; the PNG is truncated.");
}

// The IHDR chunk right after the signature carries width and height as
// big-endian uint32s at byte offsets 16 and 20.
const width = bytes.readUInt32BE(16);
const height = bytes.readUInt32BE(20);
if (width !== 1024 || height !== 1024) {
  throw new Error(`output entry.png is ${width}x${height}, not the required 1024x1024.`);
}
