# 🚀 FLOORPLAN GENIE - QUICK START GUIDE

## Production-Grade Floor Plan Analysis & Rendering Engine

### ⚡ INSTANT START (Recommended)

**Double-click to run:**
```
run_production.bat
```

This will:
- Install all dependencies automatically
- Start the production engine
- Open web interface at http://localhost:5000

---

## 🎯 WHAT YOU GET

### ✅ Advanced CAD Processing
- **Multi-sheet DXF/DWG/PDF parsing** with automatic main floor plan detection
- **Layer-aware extraction** of walls, doors, windows, restricted zones, entrances
- **Automatic scaling** and unit conversion from CAD dimensions
- **Geometric validation** and error correction

### ✅ Intelligent Îlot Placement
- **4 Coverage Profiles**: 10%, 25%, 30%, 35% with intelligent size distribution
- **Architectural Awareness**: Îlots touch walls (except near entrances), avoid restricted zones
- **Color-Coded Categories**: Small (green), Medium (blue), Large (orange), XLarge (red)
- **Optimization Algorithms**: Grid-based, random, and edge-following placement

### ✅ Corridor Network Generation
- **Mandatory corridors** between facing îlot rows
- **Graph-based optimization** using minimum spanning tree algorithms
- **Configurable width** (0.8m - 3.0m, default 1.2m)
- **Area labeling** with precise measurements

### ✅ Pixel-Perfect Rendering
- **Professional colors**: Walls (#6B7280), Restricted (#3B82F6), Entrances (#EF4444), Corridors (#F472B6)
- **Architectural line weights** and proper spacing
- **Interactive legend** and dimension annotations
- **300 DPI high-resolution** print-ready output

---

## 📋 USAGE STEPS

### 1. Start the Engine
```bash
run_production.bat
```

### 2. Open Web Interface
Navigate to: **http://localhost:5000**

### 3. Upload CAD File
- Drag & drop or select DXF, DWG, or PDF file (max 64MB)
- Supports multi-sheet documents

### 4. Configure Parameters
- **Îlot Dimensions**: e.g., "2x2,3x2,4x2,3x3,4x3,5x3,4x4,5x4"
- **Coverage Profile**: Low/Medium/High/Maximum (10%-35%)
- **Corridor Width**: 0.8m - 3.0m (default: 1.2m)
- **Layer Names**: Wall layer, restricted layer, entrance layer

### 5. Generate Plan
Click "Generate Professional Floor Plan" and wait for processing

### 6. View Results
- Interactive visualization with measurements
- Color-coded îlots and corridors
- Professional legend and annotations
- Download high-resolution PNG

---

## 🔧 ALTERNATIVE STARTUP METHODS

### Manual Python Execution
```bash
pip install -r requirements.txt
python app_production.py
```

### API Usage
```python
import requests

files = {'file': open('floorplan.dxf', 'rb')}
data = {
    'islands': '2x2,3x2,4x2,3x3,4x3,5x3,4x4,5x4',
    'corridor_width': 1.2,
    'coverage_profile': 'medium',
    'wall_layer': '0',
    'prohibited_layer': 'PROHIBITED',
    'entrance_layer': 'ENTRANCE'
}

response = requests.post('http://localhost:5000/api/process', 
                        files=files, data=data)
result = response.json()
```

---

## 📁 PROJECT STRUCTURE

```
FLOORPLAN_GENIE/
├── 🚀 run_production.bat          # START HERE - Main launcher
├── 📖 START_HERE.md               # This quick start guide
├── 📖 README_PRODUCTION.md        # Comprehensive documentation
├── ⚙️ production_engine.py         # Main production engine
├── 🌐 app_production.py           # Flask web application
├── 📋 requirements.txt            # Dependencies
├── parsers/
│   └── 🔍 advanced_cad_parser.py  # Multi-format CAD parser
├── geometry/
│   └── 🏗️ advanced_processor.py   # Architectural processor
├── layout/
│   └── 🎯 intelligent_optimizer.py # Îlot placement engine
├── visualization/
│   └── 🎨 pixel_perfect_renderer.py # Professional renderer
├── templates/
│   └── 🖥️ index_production.html   # Web interface
├── static/                        # Generated floor plans
└── uploads/                       # Temporary file storage
```

---

## 🎯 EXAMPLE WORKFLOW

1. **Upload**: `apartment_plan.dxf` (15MB DXF file)
2. **Configure**: Medium coverage (25%), 1.2m corridors
3. **Process**: ~45 seconds for full pipeline
4. **Result**: Professional floor plan with:
   - 12 intelligently placed îlots
   - 3 connecting corridors (total 18.5m²)
   - Color-coded by size categories
   - Measurements and legend
   - 300 DPI high-resolution output

---

## ⚠️ SYSTEM REQUIREMENTS

- **OS**: Windows 10/11, macOS, Linux
- **Python**: 3.8+ (auto-installed if missing)
- **RAM**: 4GB minimum, 8GB recommended
- **Storage**: 2GB free space
- **Network**: Internet for initial dependency installation

---

## 🆘 TROUBLESHOOTING

### Engine Won't Start
```bash
# Check Python installation
python --version

# Manual dependency install
pip install -r requirements.txt

# Run directly
python app_production.py
```

### File Upload Issues
- Max file size: 64MB
- Supported formats: DXF, DWG, PDF
- Check layer names match your CAD file

### Poor Results
- Verify layer configuration
- Adjust coverage profile
- Check îlot dimensions format
- Ensure sufficient usable area

---

## 🎉 SUCCESS INDICATORS

When working correctly, you'll see:
- ✅ "Production Engine" startup message
- ✅ Web interface at http://localhost:5000
- ✅ File upload and processing without errors
- ✅ Generated floor plan with colored îlots and corridors
- ✅ Professional rendering with measurements

---

## 📞 SUPPORT

For issues or questions:
1. Check `README_PRODUCTION.md` for detailed documentation
2. Verify system requirements and dependencies
3. Test with provided sample files in `input_files/`

**Ready to transform your CAD files into intelligent floor plans!** 🏗️✨