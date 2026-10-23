// 60-30-10 check (A-3). Usage: node --experimental-strip-types scripts/eval/palette.ts shot.png ["#FFFDF5,#FFFFFF,#FF6B6B"]
import { createRequire } from "node:module";
import { scorePixels, ROLE_STRING, selfTest } from "./palette-core.ts";

interface SharpResult { data: Uint8Array; info: { channels: number } }
interface SharpPipeline {
  removeAlpha(): SharpPipeline;
  raw(): SharpPipeline;
  toBuffer(options: { resolveWithObject: true }): Promise<SharpResult>;
}
type SharpFactory = (input: string) => SharpPipeline;

async function main(): Promise<void> {
  const [file, roles] = process.argv.slice(2);
  if (file === "--self-test" && roles === undefined) {
    selfTest();
    console.log(JSON.stringify({ selfTest: "passed" }));
    return;
  }
  if (!file) throw new Error(`Usage: palette.ts <image> [${ROLE_STRING}] or palette.ts --self-test`);
  if (roles !== undefined && roles !== ROLE_STRING) throw new Error(`Unsupported roles; this gate requires ${ROLE_STRING}`);

  const require = createRequire(new URL("../../frontend/package.json", import.meta.url));
  const sharp = require("sharp") as SharpFactory;
  const { data, info } = await sharp(file).removeAlpha().raw().toBuffer({ resolveWithObject: true });
  const result = scorePixels(data, info.channels);
  console.log(JSON.stringify(result));
  process.exitCode = result.ok ? 0 : 1;
}

main();
