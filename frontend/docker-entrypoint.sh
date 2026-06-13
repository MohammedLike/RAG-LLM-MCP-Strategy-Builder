#!/bin/sh
set -e
# Keep node_modules in sync when package.json changes (bind-mount dev setup)
npm install
exec npm run dev -- --host 0.0.0.0 --port 5075
