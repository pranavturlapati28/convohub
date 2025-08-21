#!/bin/bash

echo "🚀 Setting up ConvoHub Frontend..."

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js 18+ first."
    exit 1
fi

# Check Node.js version
NODE_VERSION=$(node -v | cut -d'v' -f2 | cut -d'.' -f1)
if [ "$NODE_VERSION" -lt 18 ]; then
    echo "❌ Node.js version 18+ is required. Current version: $(node -v)"
    exit 1
fi

echo "✅ Node.js version: $(node -v)"

# Install dependencies
echo "📦 Installing dependencies..."
npm install

if [ $? -ne 0 ]; then
    echo "❌ Failed to install dependencies"
    exit 1
fi

echo "✅ Dependencies installed successfully"

# Check if backend is running
echo "🔍 Checking backend connection..."
if curl -s http://127.0.0.1:8000/health > /dev/null; then
    echo "✅ Backend is running on http://127.0.0.1:8000"
else
    echo "⚠️  Backend is not running on http://127.0.0.1:8000"
    echo "   Make sure to start the ConvoHub backend first:"
    echo "   cd .. && uvicorn app.main:app --reload --host 127.0.0.1 --port 8000"
fi

echo ""
echo "🎉 Setup complete!"
echo ""
echo "To start the development server:"
echo "   npm run dev"
echo ""
echo "Then open http://localhost:3000 in your browser"
echo ""
echo "The app will work in demo mode without the backend."
echo "For full functionality, make sure the backend is running."
