import assert from "node:assert/strict";
import { readFileSync, readdirSync } from "node:fs";
import { createRequire } from "node:module";
import path from "node:path";
import test from "node:test";
import vm from "node:vm";

const require = createRequire(import.meta.url);
const typescript = require("../../node_modules/typescript");
const configSource = readFileSync(new URL("../../playwright.config.ts", import.meta.url), "utf8");
const e2eDirectory = new URL("../", import.meta.url);

function loadConfig(env = {}) {
  const output = typescript.transpileModule(configSource, {
    compilerOptions: { module: typescript.ModuleKind.CommonJS, target: typescript.ScriptTarget.ES2022 },
  }).outputText;
  const configModule = { exports: {} };
  const context = {
    exports: configModule.exports,
    module: configModule,
    process: { env },
    URL,
    require: (specifier) => {
      assert.equal(specifier, "@playwright/test");
      return {
        defineConfig: (config) => config,
        devices: { "iPhone 13": { browserName: "webkit", hasTouch: true, isMobile: true } },
      };
    },
  };
  vm.runInNewContext(output, context, { filename: "playwright.config.ts" });
  return configModule.exports.default;
}

function specFiles(directory = e2eDirectory, parent = "") {
  return readdirSync(directory, { withFileTypes: true }).flatMap((entry) => {
    const relative = path.posix.join(parent, entry.name);
    const child = new URL(`${entry.name}/`, directory);
    if (entry.isDirectory()) return specFiles(child, relative);
    return entry.isFile() && entry.name.endsWith(".spec.ts") ? [relative] : [];
  }).sort();
}

function asPatterns(patterns) {
  if (patterns === undefined) return [];
  return Array.isArray(patterns) ? patterns : [patterns];
}

function matches(pattern, file) {
  if (pattern instanceof RegExp) return pattern.test(file);
  const glob = String(pattern);
  let source = "";
  for (let index = 0; index < glob.length; index += 1) {
    const character = glob[index];
    if (character === "*" && glob[index + 1] === "*") {
      index += 1;
      if (glob[index + 1] === "/") {
        index += 1;
        source += "(?:.*/)?";
      } else source += ".*";
    } else if (character === "*") source += "[^/]*";
    else if (character === "?") source += "[^/]";
    else source += character.replace(/[.+^${}()|[\]\\]/g, "\\$&");
  }
  return new RegExp(`^${source}$`).test(file);
}

function projectsForFile(config, file) {
  return Array.from(config.projects).filter((project) => {
    const includes = asPatterns(project.testMatch ?? config.testMatch).some((pattern) => matches(pattern, file));
    const ignores = asPatterns(project.testIgnore ?? config.testIgnore).some((pattern) => matches(pattern, file));
    return includes && !ignores;
  }).map(({ name }) => name);
}

const plain = (value) => JSON.parse(JSON.stringify(value));

const expectedViewports = {
  "mobile-320": { width: 320, height: 568 },
  "mobile-375": { width: 375, height: 812 },
  "tablet-768": { width: 768, height: 1024 },
  "desktop-1440": { width: 1440, height: 900 },
  "ultrawide-32x9": { width: 5120, height: 1440 },
};
const guideFiles = ["nb-primitives.spec.ts", "motion-hooks.spec.ts"];

test("production selection assigns every app spec to its viewport projects once", () => {
  const config = loadConfig({ PLAYWRIGHT_PORT: "3117" });
  const files = specFiles();
  const guide = new Set(guideFiles);
  const realStackFiles = files.filter((file) => file === "real-stack.spec.ts");
  const visualFiles = files.filter((file) => file === "visual-regression.spec.ts");
  const appFiles = files.filter((file) =>
    !guide.has(path.posix.basename(file)) &&
    !realStackFiles.includes(file) &&
    !visualFiles.includes(file));
  const standardNames = Object.keys(expectedViewports);

  assert.deepEqual(Array.from(config.projects, ({ name }) => name), standardNames);
  assert.equal(config.use.baseURL, "http://localhost:3117");
  assert.match(config.webServer.command, /npm run start/);
  assert.doesNotMatch(config.webServer.command, /npm run dev/);
  assert.equal(config.projects.length, standardNames.length);
  assert.equal(config.webServer.env, undefined);

  for (const project of config.projects) {
    assert.deepEqual(plain(project.use.viewport), expectedViewports[project.name]);
  }

  for (const file of appFiles) assert.deepEqual(projectsForFile(config, file), standardNames, file);
  for (const file of realStackFiles) assert.deepEqual(projectsForFile(config, file), [], file);
  for (const file of visualFiles) assert.deepEqual(projectsForFile(config, file), [], file);
  for (const file of files.filter((entry) => guide.has(path.posix.basename(entry)))) {
    assert.deepEqual(projectsForFile(config, file), [], file);
  }
});

test("guide mode selects only development guide specs across matching viewports", () => {
  const config = loadConfig({ PLAYWRIGHT_MODE: "guide", PLAYWRIGHT_PORT: "3123" });
  const files = specFiles();
  const expectedNames = Object.keys(expectedViewports).map((name) => `guide-${name}`);
  const expectedGuideFiles = files.filter((file) => guideFiles.includes(path.posix.basename(file)));

  assert.deepEqual(Array.from(config.projects, ({ name }) => name), expectedNames);
  assert.equal(config.projects.length, expectedNames.length);
  assert.equal(config.use.baseURL, "http://localhost:3123");
  assert.match(config.webServer.command, /npm run dev/);
  assert.doesNotMatch(config.webServer.command, /npm run start/);
  for (const project of config.projects) {
    const viewportName = project.name.slice("guide-".length);
    assert.deepEqual(plain(project.use.viewport), expectedViewports[viewportName]);
  }
  for (const file of expectedGuideFiles) assert.deepEqual(projectsForFile(config, file), expectedNames, file);
  for (const file of files.filter((entry) => !expectedGuideFiles.includes(entry))) {
    assert.deepEqual(projectsForFile(config, file), [], file);
  }
});

test("visual mode selects only the 375px and 1440px visual regression projects", () => {
  const config = loadConfig({ PLAYWRIGHT_MODE: "visual", PLAYWRIGHT_PORT: "3127" });
  const files = specFiles();
  const visualFiles = files.filter((file) => file === "visual-regression.spec.ts");
  const expectedNames = ["mobile-375", "desktop-1440"];

  assert.deepEqual(Array.from(config.projects, ({ name }) => name), expectedNames);
  assert.equal(config.projects.length, expectedNames.length);
  assert.equal(config.use.baseURL, "http://localhost:3127");
  assert.match(config.webServer.command, /npm run start/);
  assert.doesNotMatch(config.webServer.command, /npm run dev/);
  assert.deepEqual(visualFiles, ["visual-regression.spec.ts"]);
  assert.deepEqual(
    plain(config.projects.map(({ use }) => use.viewport)),
    [expectedViewports["mobile-375"], expectedViewports["desktop-1440"]],
  );
  assert.equal(config.projects[0].use.browserName, "chromium");
  assert.equal(config.projects[0].use.isMobile, true);
  assert.equal(config.projects[0].use.hasTouch, true);
  for (const file of visualFiles) assert.deepEqual(projectsForFile(config, file), expectedNames, file);
  for (const file of files.filter((entry) => !visualFiles.includes(entry))) {
    assert.deepEqual(projectsForFile(config, file), [], file);
  }
});

test("real-stack mode is explicit, loopback guarded, and selects only its two preserved viewports", () => {
  assert.throws(() => loadConfig({ PLAYWRIGHT_MODE: "real-stack" }), /PLAYWRIGHT_REAL_STACK_API_URL is required/);
  for (const url of [
    "http://127.0.0.1:18001",
    "https://127.0.0.1:18000",
    "http://example.test:18000",
    "http://user@127.0.0.1:18000",
  ]) {
    assert.throws(() => loadConfig({ PLAYWRIGHT_MODE: "real-stack", PLAYWRIGHT_REAL_STACK_API_URL: url }), /disposable loopback URL/);
  }

  const apiUrl = "http://127.0.0.1:18000";
  const config = loadConfig({
    PLAYWRIGHT_MODE: "real-stack",
    PLAYWRIGHT_REAL_STACK_API_URL: apiUrl,
    PLAYWRIGHT_PORT: "3130",
  });
  const files = specFiles();
  const realStackFiles = files.filter((file) => file === "real-stack.spec.ts");
  const expectedNames = ["real-stack", "real-stack-mobile-375"];
  const desktop = config.projects.find(({ name }) => name === "real-stack");
  const mobile = config.projects.find(({ name }) => name === "real-stack-mobile-375");

  assert.deepEqual(Array.from(config.projects, ({ name }) => name), expectedNames);
  assert.deepEqual(plain(desktop.use.viewport), { width: 1440, height: 900 });
  assert.deepEqual(plain(mobile.use.viewport), { width: 375, height: 812 });
  assert.equal(mobile.use.browserName, "chromium");
  assert.equal(mobile.use.isMobile, true);
  assert.equal(mobile.use.hasTouch, true);
  assert.equal(config.use.baseURL, "http://localhost:3130");
  assert.match(config.webServer.command, /NEXT_PUBLIC_API_URL=http:\/\/127\.0\.0\.1:18000 npm run build/);
  assert.match(config.webServer.command, /NEXT_PUBLIC_API_URL=http:\/\/127\.0\.0\.1:18000 npm run start/);
  assert.equal(plain(config.webServer.env).NEXT_PUBLIC_API_URL, apiUrl);
  assert.equal(config.webServer.reuseExistingServer, false);
  for (const file of realStackFiles) assert.deepEqual(projectsForFile(config, file), expectedNames, file);
  for (const file of files.filter((entry) => !realStackFiles.includes(entry))) {
    assert.deepEqual(projectsForFile(config, file), [], file);
  }
});
