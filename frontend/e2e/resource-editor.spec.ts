import { expect, test as base, type Page } from "./mock-platform";

const unexpectedByPage = new WeakMap<Page, string[]>();
const test = base.extend<{ apiGuard: void }>({
  apiGuard: [async ({ page }, use) => {
    const unexpected: string[] = [];
    unexpectedByPage.set(page, unexpected);
    await use();
    expect(unexpected).toEqual([]);
  }, { auto: true }],
});

const pilot = { id: 7, name: "Pilot", season: 2026 };

async function setup(page: Page, options: {
  saveStatus?: number;
  saveStatuses?: number[];
  deferSave?: boolean;
} = {}) {
  let postCount = 0;
  let deleteCount = 0;
  let posted: unknown;
  let releaseSave: (() => void) | undefined;
  const unexpected = unexpectedByPage.get(page)!;
  await page.route("**/api/**", async (route) => {
    const request = route.request();
    const url = new URL(request.url());
    if (request.method() === "GET" && url.pathname === "/api/championships") {
      await route.fulfill({ json: [pilot] });
    } else if (request.method() === "GET" && url.pathname === "/api/auth/me") {
      await route.fulfill({ json: { id: 1, email: "qa@example.test", full_name: "QA", role: "ADMIN" } });
    } else if (request.method() === "GET" && url.pathname === "/api/dashboard") {
      await route.fulfill({ json: { active_sessions: 0, scheduled_events: 0, open_incidents: 0, drivers: 0 } });
    } else if (request.method() === "GET") {
      await route.fulfill({ json: [] });
    } else if (request.method() === "POST" && url.pathname === "/api/championships") {
      postCount += 1;
      posted = request.postDataJSON();
      if (options.deferSave) {
        await new Promise<void>((resolve) => { releaseSave = resolve; });
      }
      const status = options.saveStatuses?.[postCount - 1] ?? options.saveStatus ?? 201;
      await route.fulfill({
        status,
        json: status >= 400 ? { detail: "Service unavailable" } : { ...pilot, ...posted as object },
      });
    } else if (request.method() === "DELETE" && url.pathname === "/api/championships/7") {
      deleteCount += 1;
      await route.fulfill({ status: 204, body: "" });
    } else {
      unexpected.push(`${request.method()} ${url.pathname}`);
      await route.fulfill({ status: 405, json: { detail: "Unexpected test request" } });
    }
  });
  await page.goto("/championships");
  return {
    counts: () => ({ postCount, deleteCount }),
    payload: () => posted,
    release: () => releaseSave?.(),
  };
}

async function openCreate(page: Page) {
  await page.getByRole("button", { name: "New record" }).click();
  return page.getByRole("dialog", { name: "Create record" });
}

test("required resource fields prevent an empty POST", async ({ page }) => {
  const api = await setup(page);
  const dialog = await openCreate(page);
  const name = dialog.getByRole("textbox", { name: "name" });
  const season = dialog.getByRole("spinbutton", { name: "season" });
  await expect(name).toHaveAttribute("required", "");
  await expect(season).toHaveAttribute("required", "");
  await dialog.getByRole("button", { name: "Save record" }).click();
  await expect(name).toBeFocused();
  expect(api.counts().postCount).toBe(0);
});

test("valid zero season posts the typed payload and closes on success", async ({ page }) => {
  const api = await setup(page);
  const dialog = await openCreate(page);
  await dialog.getByRole("textbox", { name: "name" }).fill("Formula One");
  await dialog.getByRole("spinbutton", { name: "season" }).fill("0");
  await dialog.getByRole("button", { name: "Save record" }).click();
  await expect(dialog).toBeHidden();
  expect(api.payload()).toEqual({ name: "Formula One", season: 0 });
  expect(api.counts().postCount).toBe(1);
});

test("native field errors stay linked and clear before a valid zero season save", async ({ page }) => {
  const api = await setup(page);
  const dialog = await openCreate(page);
  const name = dialog.getByRole("textbox", { name: "name" });
  const season = dialog.getByRole("spinbutton", { name: "season" });
  await expect(name).not.toHaveAttribute("aria-invalid");

  const linkedError = async (field: typeof name) => {
    const describedBy = await field.getAttribute("aria-describedby");
    const errorId = describedBy?.split(/\s+/).find((id) => id.endsWith("-error"));
    expect(errorId).toBeTruthy();
    const error = dialog.locator(`[id="${errorId}"]`);
    await expect(error).toHaveAttribute("role", "alert");
    await expect(error).toHaveText(await field.evaluate((input) => (input as HTMLInputElement).validationMessage));
    return error;
  };

  await name.focus();
  await expect(name).toBeFocused();
  await season.focus();
  await expect(name).toHaveAttribute("aria-invalid", "true");
  const nameError = await linkedError(name);
  await name.fill("Formula One");
  await expect(name).not.toHaveAttribute("aria-invalid");
  await expect(nameError).toHaveCount(0);

  await dialog.getByRole("button", { name: "Save record" }).click();
  await expect(season).toHaveAttribute("aria-invalid", "true");
  const seasonError = await linkedError(season);
  expect(api.counts().postCount).toBe(0);
  await season.fill("0");
  await expect(season).not.toHaveAttribute("aria-invalid");
  await expect(seasonError).toHaveCount(0);
  await dialog.getByRole("button", { name: "Save record" }).click();
  await expect(dialog).toBeHidden();
  expect(api.payload()).toEqual({ name: "Formula One", season: 0 });
  expect(api.counts().postCount).toBe(1);
});

test("deferred save disables submit and coalesces same-frame clicks", async ({ page }) => {
  const api = await setup(page, { deferSave: true });
  const dialog = await openCreate(page);
  await dialog.getByRole("textbox", { name: "name" }).fill("Formula One");
  await dialog.getByRole("spinbutton", { name: "season" }).fill("0");
  const save = dialog.getByRole("button", { name: "Save record" });
  await save.evaluate((button) => {
    const submit = button as HTMLButtonElement;
    for (let i = 0; i < 20; i += 1) submit.click();
  });
  await expect(dialog.getByRole("button", { name: "Saving…" })).toBeDisabled();
  expect(api.counts().postCount).toBe(1);
  api.release();
  await expect(dialog).toBeHidden();
});

test("failed POST preserves values and cause for a successful retry", async ({ page }) => {
  const api = await setup(page, { saveStatuses: [503, 201] });
  const dialog = await openCreate(page);
  await dialog.getByRole("textbox", { name: "name" }).fill("Formula One");
  await dialog.getByRole("spinbutton", { name: "season" }).fill("0");
  await dialog.getByRole("button", { name: "Save record" }).click();
  await expect(dialog.getByRole("alert")).toContainText("Service unavailable");
  await expect(dialog.getByRole("textbox", { name: "name" })).toHaveValue("Formula One");
  await expect(dialog.getByRole("spinbutton", { name: "season" })).toHaveValue("0");
  await expect(dialog).toBeVisible();
  await dialog.getByRole("button", { name: "Save record" }).click();
  await expect(dialog).toBeHidden();
  expect(api.counts().postCount).toBe(2);
  expect(api.counts().deleteCount).toBe(0);
});

test("T382-DELETE requires confirmation before writing", async ({ page }) => {
  const api = await setup(page);
  await page.getByRole("row").filter({ hasText: "Pilot" }).click();
  const details = page.getByRole("dialog", { name: "Record details" });
  await details.getByRole("button", { name: "Delete record" }).click();
  const confirmation = page.getByRole("dialog", { name: /delete/i });
  await expect(confirmation).toBeVisible();
  expect(api.counts().deleteCount).toBe(0);
  await confirmation.getByRole("button", { name: "Cancel" }).click();
  await expect(confirmation).toBeHidden();
  expect(api.counts().deleteCount).toBe(0);
  await details.getByRole("button", { name: "Delete record" }).click();
  await page.getByRole("dialog", { name: /delete/i }).getByRole("button", { name: "Delete record" }).evaluate((button) => {
    for (let i = 0; i < 20; i += 1) (button as HTMLButtonElement).click();
  });
  await expect.poll(() => api.counts().deleteCount).toBe(1);
});

test("T382 row edit buttons open one populated details dialog without writing", async ({ page }) => {
  const api = await setup(page);
  const row = page.getByRole("row").filter({ hasText: "Pilot" });
  await row.getByRole("button", { name: "Edit record" }).click();
  const details = page.getByRole("dialog", { name: "Record details" });
  await expect(details).toBeVisible();
  await expect(details.getByRole("textbox", { name: "name" })).toHaveValue("Pilot");
  await expect(details.getByRole("spinbutton", { name: "season" })).toHaveValue("2026");
  await expect(page.getByRole("dialog")).toHaveCount(1);

  await page.keyboard.press("Escape");
  const edit = row.getByRole("button", { name: "Edit record" });
  await expect(details).toHaveCount(0);
  await edit.focus();
  await expect(edit).toBeFocused();
  await page.keyboard.press("Enter");
  await expect(details).toBeVisible();
  await expect(page.getByRole("dialog")).toHaveCount(1);
  expect(api.counts()).toEqual({ postCount: 0, deleteCount: 0 });
});

test("T382 row delete cancel restores details without writing", async ({ page }) => {
  const api = await setup(page);
  const row = page.getByRole("row").filter({ hasText: "Pilot" });
  await row.getByRole("button", { name: "Delete record" }).click();
  const confirmation = page.getByRole("dialog", { name: "Delete record" });
  await expect(confirmation).toBeVisible();
  expect(api.counts()).toEqual({ postCount: 0, deleteCount: 0 });
  await confirmation.getByRole("button", { name: "Cancel" }).click();

  const details = page.getByRole("dialog", { name: "Record details" });
  await expect(confirmation).toBeHidden();
  await expect(details).toBeVisible();
  await expect(page.locator("[data-primary='true']")).toHaveAccessibleName("Save record");
  expect(api.counts()).toEqual({ postCount: 0, deleteCount: 0 });
  await page.keyboard.press("Escape");
  await expect(details).toBeHidden();
  await expect(page.locator("[data-primary='true']")).toHaveAccessibleName("New record");
  await expect(page.locator("[data-primary='true']")).toHaveCount(1);
});

test("T382 primary action follows the active resource dialog", async ({ page }) => {
  await setup(page);
  const expectPrimary = async (label: string) => {
    const primary = page.locator("[data-primary='true']");
    await expect(primary).toHaveCount(1);
    await expect(primary).toHaveAccessibleName(label);
    await expect(primary).toBeVisible();
  };

  await expectPrimary("New record");
  const create = await openCreate(page);
  await expectPrimary("Save record");
  await page.keyboard.press("Escape");
  await expect(create).toBeHidden();
  await expectPrimary("New record");

  await page.getByRole("row").filter({ hasText: "Pilot" }).click();
  const details = page.getByRole("dialog", { name: "Record details" });
  await expectPrimary("Save record");
  await details.getByRole("button", { name: "Delete record" }).click();
  const confirmation = page.getByRole("dialog", { name: "Delete record" });
  await expect(confirmation).toBeVisible();
  await expectPrimary("Delete record");
  await confirmation.getByRole("button", { name: "Cancel" }).click();
  await expect(confirmation).toBeHidden();
  await expectPrimary("Save record");
  await page.keyboard.press("Escape");
  await expect(details).toBeHidden();
  await expectPrimary("New record");
});
