import { expect, test } from "@playwright/test";

async function isolatePlaywrightData(page) {
  await page.goto("/");
  await page.getByTestId("search-input").fill("Playwright");
  await expect(page.getByTestId("journey-row")).toHaveCount(2, { timeout: 10000 });
}

test("loads the real dashboard with the seeded journeys", async ({ page }) => {
  await isolatePlaywrightData(page);

  await expect(page.getByTestId("app-shell")).toBeVisible();
  await expect(page.getByTestId("search-panel")).toBeVisible();
  await expect(page.getByTestId("headline-card")).toBeVisible();
  await expect(page.getByTestId("journey-map-panel")).toBeVisible();
  await expect(page.getByTestId("journey-table")).toBeVisible();
  await expect(page.getByTestId("api-status-badge")).toBeVisible();
  await expect(page.getByTestId("journey-row")).toHaveCount(2);
  await expect(page.getByTestId("selected-journey-card")).toContainText("Playwright Rail");
});

test("filters the real dataset by service type", async ({ page }) => {
  await isolatePlaywrightData(page);

  await page.getByTestId("service-filter").selectOption("Jour");

  await expect(page.getByTestId("journey-row")).toHaveCount(1, { timeout: 10000 });
  await expect(page.getByTestId("journey-table")).toContainText("Playwright City Beta");
  await expect(page.getByTestId("journey-table")).toContainText("Playwright City Gamma");
  await expect(page.getByTestId("journey-table")).not.toContainText("Playwright City Alpha");
});

test("changes the active trip from the real table selection", async ({ page }) => {
  await isolatePlaywrightData(page);

  await page.getByTestId("journey-select-playwright-day-2026").click();

  await expect(page.getByTestId("selected-journey-card")).toContainText("Playwright Rail");
  await expect(page.getByTestId("selected-journey-card")).toContainText(
    "Playwright City Beta -> Playwright City Gamma"
  );
});
