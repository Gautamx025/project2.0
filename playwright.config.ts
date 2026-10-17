import {defineConfig} from '@playwright/test';
const python = process.platform==='win32'?'.venv\\Scripts\\python.exe':'.venv/bin/python';
export default defineConfig({
  testDir:'./tests/e2e', fullyParallel:false, workers:1, timeout:60000,
  expect:{timeout:15000}, reporter:'list',
  use:{baseURL:'http://127.0.0.1:3000',viewport:{width:1440,height:1000},trace:'retain-on-failure',screenshot:'only-on-failure',reducedMotion:'reduce'},
  webServer:[
    {command:`${python} -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000`,url:'http://127.0.0.1:8000/api/health',reuseExistingServer:!process.env.CI,timeout:60000},
    {command:'npm run dev --workspace frontend',url:'http://127.0.0.1:3000',reuseExistingServer:!process.env.CI,timeout:120000}
  ]
});
