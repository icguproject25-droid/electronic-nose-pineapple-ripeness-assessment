#!/usr/bin/env node

/**
 * Farmer App Smoke Test
 *
 * 這個測試用來確認目前資料夾已經依照
 * Tinazhen/Farmer_pineapple/expo 的主要架構建立完成。
 *
 * 執行方式：
 *   npm run test
 */

const fs = require('fs');
const path = require('path');

const root = path.resolve(__dirname, '..');

const requiredFiles = [
  'package.json',
  'app.json',
  'tsconfig.json',
  'README.md',
  'app/_layout.tsx',
  'app/login.tsx',
  'app/modal.tsx',
  'app/(tabs)/_layout.tsx',
  'app/(tabs)/index.tsx',
  'app/(tabs)/batches.tsx',
  'app/(tabs)/scan.tsx',
  'app/(tabs)/reports.tsx',
  'app/(tabs)/settings.tsx',
  'app/batches/create.tsx',
  'app/batches/[batchId]/index.tsx',
  'app/batches/[batchId]/scan.tsx',
  'app/batches/[batchId]/summary.tsx',
  'components/AppButton.tsx',
  'components/DemoScrollView.tsx',
  'constants/i18n.ts',
  'constants/theme.ts',
  'screens/LoginScreen.tsx',
  'screens/HomeScreen.tsx',
  'screens/BatchesScreen.tsx',
  'screens/ScanEntryScreen.tsx',
  'screens/CreateBatchScreen.tsx',
  'screens/BatchDetailScreen.tsx',
  'screens/BatchScanScreen.tsx',
  'screens/BatchSummaryScreen.tsx',
  'screens/ReportsScreen.tsx',
  'screens/SettingsScreen.tsx',
  'store/app-store.tsx',
  'types/models.ts',
  'utils/helpers.ts'
];

function pass(message) {
  console.log(`PASS ${message}`);
}

function fail(message) {
  console.error(`FAIL ${message}`);
  process.exitCode = 1;
}

for (const file of requiredFiles) {
  const fullPath = path.join(root, file);
  if (fs.existsSync(fullPath)) pass(`${file} exists`);
  else fail(`${file} is missing`);
}

const packageJson = JSON.parse(fs.readFileSync(path.join(root, 'package.json'), 'utf8'));
for (const scriptName of ['start', 'start-web', 'lint', 'test']) {
  if (packageJson.scripts && packageJson.scripts[scriptName]) pass(`package.json script ${scriptName} exists`);
  else fail(`package.json script ${scriptName} is missing`);
}

if (process.exitCode === 1) {
  console.error('\nSmoke test failed. Please check the missing files above.');
} else {
  console.log('\nSmoke test passed. Farmer app cloned structure is complete.');
}
