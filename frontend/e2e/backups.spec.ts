import { test, expect } from '@playwright/test';

// Parent BS-027 / ADR-0032: on-demand backup is available to the coaching staff.
test('manual backup shows a verified copy and its location', async ({ page }) => {
  await page.goto('/');
  await page.getByRole('button', { name: 'Back up Workspace', exact: true }).click();
  await expect(page.getByRole('status')).toContainText('Verified backup saved');
  await expect(page.getByRole('status')).toContainText('backups directory: manual-');
  await page.screenshot({ path: '/tmp/nimbus-8-backup-notice.png', fullPage: true });
});
