#!/bin/bash

# Floorplan Genie Production Deployment Script

echo "🚀 FLOORPLAN GENIE - PRODUCTION DEPLOYMENT"
echo "=========================================="

# Check if git is initialized
if [ ! -d ".git" ]; then
    echo "📦 Initializing Git repository..."
    git init
    git branch -M main
fi

# Add all files
echo "📁 Adding files to Git..."
git add .

# Commit changes
echo "💾 Committing changes..."
git commit -m "Production-ready Floorplan Genie with full CAD processing pipeline

Features:
- Advanced CAD file processing (DXF, DWG, PDF)
- Intelligent îlot placement with multiple algorithms
- Pixel-perfect rendering with professional standards
- Corridor network generation with graph algorithms
- Production Flask API with comprehensive error handling
- Modern responsive web interface
- Docker containerization
- Render.com deployment configuration

Technical Stack:
- Flask + Gunicorn production server
- Shapely + NetworkX for geometric processing
- Matplotlib for professional rendering
- OpenCV for PDF computer vision
- Tailwind CSS for modern UI
- Docker for containerization"

# Add remote if not exists
if ! git remote get-url origin > /dev/null 2>&1; then
    echo "🔗 Adding GitHub remote..."
    git remote add origin https://github.com/rehmanul/CADGinie-August.git
fi

# Push to GitHub
echo "⬆️ Pushing to GitHub..."
git push -u origin main --force

echo ""
echo "✅ DEPLOYMENT COMPLETE!"
echo ""
echo "🌐 GitHub Repository: https://github.com/rehmanul/CADGinie-August"
echo "🚀 Deploy to Render.com:"
echo "   1. Connect your GitHub repo to Render.com"
echo "   2. Use the render.yaml configuration"
echo "   3. Set environment variables as needed"
echo ""
echo "🐳 Docker Deployment:"
echo "   docker build -t floorplan-genie ."
echo "   docker run -p 5000:5000 floorplan-genie"
echo ""
echo "🔧 Local Development:"
echo "   pip install -r requirements.txt"
echo "   python production_app.py"
echo ""
echo "📚 API Endpoints:"
echo "   POST /api/upload - Upload CAD file"
echo "   POST /api/process - Process floor plan"
echo "   GET /api/health - Health check"
echo "   GET /api/capabilities - System capabilities"
echo ""