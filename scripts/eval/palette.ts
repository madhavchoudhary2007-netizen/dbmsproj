// 60-30-10 check (A-3). Usage: npx tsx scripts/eval/palette.ts shot.png "#ffffff,#f4f5f7,#2f5bd3"
// Roles in order: dominant, secondary, accent. Pixels far from every role (text, imagery) are excluded.
import sharp from "sharp";

async function main(): Promise<void> {
  const [file, list] = process.argv.slice(2);
  const roles = list.split(",").map(h => [1, 3, 5].map(i => parseInt(h.slice(i, i + 2), 16)));
  const { data, info } = await sharp(file).removeAlpha().raw().toBuffer({ resolveWithObject: true });
  const counts = roles.map(() => 0);
  let total = 0;
  for (let i = 0; i < data.length; i += info.channels) {
    let best = -1, bestD = Infinity;
    roles.forEach((r, k) => {
      const d = (r[0] - data[i]) ** 2 + (r[1] - data[i + 1]) ** 2 + (r[2] - data[i + 2]) ** 2;
      if (d < bestD) { bestD = d; best = k; }
    });
    if (bestD <= 900) { counts[best]++; total++; }
  }
  const share = counts.map(c => c / total);
  const ok = share[0] >= 0.5 && share[0] <= 0.7 && share[1] >= 0.2 && share[1] <= 0.4 && share[2] >= 0.05 && share[2] <= 0.15;
  console.log(JSON.stringify({ share, ok }));
  process.exit(ok ? 0 : 1);
}

main();
