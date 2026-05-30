#!/bin/bash

echo "Stopping Pineapple Smart System..."

pkill -f "app_local.py"
pkill -f "app_gateway.py"
pkill -f "pineapple_unified_web"
pkill -f "app.py"

echo "All related Python services stopped."
