#!/usr/bin/env node

/**
 * Farmer App Smoke Test
 *
 * 這是一個最小可執行測試腳本，不需要啟動 Expo，也不需要手機或模擬器。
 *
 * 測試目的：
 * 1. 檢查專案必要檔案是否存在。
 * 2. 檢查 Expo Router 必要頁面是否存在。
 * 3. 檢查 package.json 是否包含必要 scripts。
 *
 * 使用方式：
 *   npm test
 *   或
 *   node ./scripts/smoke-test.js
 */

const fs = require('fs');
const path = require('path');

const root = path.resolve(__dirname, '..');

/** 必須存在的檔案。 */
const requiredFiles = [
  'package.json',
  'app.json',
  'tsconfig.json',
  'app/_layout.tsx',
  'app/index.tsx',
  'app/batches.tsx',
  'app/batch-create.tsx',
  'app/batch-scan.tsx',
  'app/batch-summary.tsx',
  'app/reports.tsx',
  'app/settings.tsx',
  'components/BatchCard.tsx',
  'components/StatCard.tsx',
  'constants/theme.ts',
  'services/api.ts',
  'stores/farmerStore.ts',
  'types/index.ts',
  'README.md'
];

/** 輸出結果用的小工具。 */
function pass(message) {
  console.log(`PASS ${message}`);
}

function fail(message) {
  console.error(`FAIL ${message}`);
  process.exitCode = 1;
}

for (const file of requiredFiles) {
  const fullPath = path.join(root, file);
  if (fs.existsSync(fullPath)) {
    pass(`${file} exists`);
  } else {
    fail(`${file} is missing`);
  }
}

const packageJsonPath = path.join(root, 'package.json');
const packageJson = JSON.parse(fs.readFileSync(packageJsonPath, 'utf8'));

for (const scriptName of ['start', 'start-web', 'lint', 'test']) {
  if (packageJson.scripts && packageJson.scripts[scriptName]) {
    pass(`package.json script "${scriptName}" exists`);
  } else {
    fail(`package.json script "${scriptName}" is missing`);
  }
}

if (process.exitCode === 1) {
  console.error('\nSmoke test failed. Please check the missing files or scripts above.');
} else {
  console.log('\nSmoke test passed. Farmer app scaffold is complete.');
}
