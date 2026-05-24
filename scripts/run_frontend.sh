#!/bin/bash
# Helper script to run the frontend locally using python http.server on port 5000

# Get current script directory
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$DIR")"

echo "🚀 Starting RAGaaS Static Frontend..."
echo "📂 Root Directory: $PROJECT_ROOT/frontend"
echo "🌐 URL: http://localhost:5000"
echo "Press Ctrl+C to stop."

# Start serving using python3
python3 -m http.server 5000 --directory "$PROJECT_ROOT/frontend"
