#!/usr/bin/env bash
cd "$(dirname "$0")"

echo "Installing InsureFlow AI Frontend dependencies..."

npm install

echo ""
echo "Dependencies installed successfully!"
echo ""
echo "To run the frontend:"
echo "  npm run dev"
echo ""
echo "The app will be available at http://localhost:3000"