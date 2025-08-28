# Floorplan Genie - CAD Analysis & Îlot Placement Engine

Floor plan analysis and rendering engine with Autodesk Forge integration, furniture placement, and corridor network generation.

## Features

### Autodesk Forge Integration
- CAD processing with Autodesk Forge API
- Client authentication
- Multi-format support: DXF, DWG, RVT, IPT, PDF
- Thumbnail generation and metadata extraction
- Fallback processing

### CAD File Processing
- Dual-mode processing: Forge API + Standard processing
- Layer-aware extraction with computer vision
- Automatic scale detection and unit conversion
- Element classification: Walls, doors, windows, restricted zones, entrances
- Geometric validation and correction

### Îlot Placement Engine
- Multiple algorithms: Grid-based, random optimization, edge-following
- Coverage profiles: 10%, 25%, 30%, 35% configurable coverage
- Accessibility compliance checking
- Building code validation
- Optimization for usable space

### Corridor Network Generation
- Graph-based planning using minimum spanning tree algorithms
- Pathfinding optimization for circulation
- Configurable corridor widths (default 1.2m)
- Automatic area calculation and labeling
- Visual hierarchy maintenance

### Visualization
- Pixel-perfect rendering with architectural line weights
- Color-coded elements matching standards
- Interactive zoom, pan, and measurement tools
- High-resolution output (300 DPI)
- Scalable vector graphics support

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- pip package manager

### Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd FLOORPLAN_GENIE/floorplan-generator
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Run the application**
```bash
python app.py
```

4. **Access the web interface**
Open your browser and navigate to: `http://localhost:5000`

## Project Structure

```
FLOORPLAN_GENIE/
├── Applications
│   ├── app.py                          # Main entry point
│   ├── enhanced_production_app.py      # App with Forge
│   └── production_app.py               # Standard app
├── Core Engine (src/)
│   ├── processors/
│   │   ├── advanced_cad_processor.py       # Multi-format CAD processing
│   │   └── autodesk_forge_processor.py     # Forge integration
│   ├── optimizers/
│   │   └── intelligent_layout_optimizer.py # Layout placement
│   ├── renderers/
│   │   └── pixel_perfect_renderer.py       # Visualization
│   └── engines/
│       ├── production_engine.py            # Processing pipeline
│       └── enhanced_production_engine.py   # Forge-enhanced pipeline
├── Web Interface
│   ├── templates/enhanced_production_index.html
│   └── static/ (CSS, JS, assets)
├── Deployment
│   ├── Dockerfile                      # Container configuration
│   ├── render.yaml                     # Render.com deployment
│   ├── enhanced_requirements.txt       # Production dependencies
│   └── config.py                       # Environment configuration
├── uploads/                            # File upload storage
├── output_files/                       # Generated floor plans
└── Backup/                             # Legacy/unused files
```

## 🔧 Usage

### Web Interface

1. **Upload CAD File**: Drag & drop or select DXF, DWG, or PDF files
2. **Configure Parameters**:
   - Îlot dimensions (e.g., "3x2,4x3,5x4")
   - Corridor width (0.8-3.0m)
   - Coverage profile (10%-35%)
   - Layer names for walls, restricted zones, entrances
3. **Generate Plan**: Click "Generate Professional Floor Plan"
4. **View Results**: Interactive visualization with zoom, measurements, and legend
5. **Download**: High-resolution PNG or vector formats

### API Integration

```python
import requests

# Upload and process floor plan
files = {'file': open('floorplan.dxf', 'rb')}
data = {
    'islands': '3x2,4x3,5x4',
    'corridor_width': 1.2,
    'coverage_profile': 'medium',
    'wall_layer': '0',
    'prohibited_layer': 'PROHIBITED'
}

response = requests.post('http://localhost:5000/api/process', 
                        files=files, data=data)
result = response.json()

if result['success']:
    print(f"Generated plan: {result['result_url']}")
    print(f"Download: {result['download_url']}")
```

## 🎯 Configuration Options

### Coverage Profiles
- **Low (10%)**: Minimal furniture placement
- **Medium (25%)**: Balanced layout (recommended)
- **High (30%)**: Dense arrangement
- **Maximum (35%)**: Maximum utilization

### Layer Configuration
- **Wall Layer**: CAD layer containing wall elements
- **Prohibited Layer**: Restricted zones (blue areas)
- **Entrance Layer**: Doors and entrances (red areas)

### Îlot Dimensions
Format: `width×height,width×height` (in meters)
Example: `3x2,4x3,5x4,2x2`

## 🔬 Technical Details

### Processing Pipeline

1. **CAD Parsing**: Multi-format file analysis with layer extraction
2. **Geometry Processing**: Architectural element classification and validation
3. **Layout Optimization**: AI-powered îlot placement with multiple algorithms
4. **Corridor Generation**: Graph-based network optimization
5. **Professional Rendering**: High-resolution visualization with measurements

### Algorithms Used

- **Shapely**: Geometric operations and spatial analysis
- **NetworkX**: Graph algorithms for corridor networks
- **OpenCV**: Computer vision for PDF processing
- **SciPy**: Optimization methods
- **Matplotlib**: Professional visualization

### Quality Assurance

- Accessibility compliance checking (corridor widths, clearances)
- Building code validation (spacing, emergency access)
- Geometric accuracy verification
- Optimization metrics calculation

## 📊 Output Specifications

### Image Output
- **Format**: PNG (high-resolution)
- **Resolution**: 300 DPI (print-ready)
- **Color Scheme**: Professional architectural standards
- **Elements**: Walls (#6B7280), Restricted (#3B82F6), Entrances (#EF4444), Îlots (green variants), Corridors (#F472B6)

### Statistics Provided
- Total area calculation
- Îlot coverage percentage
- Corridor area and count
- Placement efficiency metrics
- Accessibility compliance status

## 🛠️ Development

### Adding New Parsers
1. Create parser in `parsers/` directory
2. Implement `parse_[format]()` function
3. Return classified entities dictionary
4. Update `core_logic.py` to support new format

### Custom Placement Algorithms
1. Add algorithm to `layout_optimizer.py`
2. Implement in `LayoutOptimizer` class
3. Update strategy selection in `_place_islands_optimized()`

### Visualization Customization
1. Modify color scheme in `visualizer.py`
2. Update line weights and styling
3. Add new element types and rendering

## 🔍 Troubleshooting

### Common Issues

**File Upload Errors**
- Check file size (max 64MB)
- Verify file format (DXF, DWG, PDF)
- Ensure file is not corrupted

**Processing Failures**
- Verify layer names match CAD file
- Check for geometric inconsistencies
- Ensure sufficient usable area

**Poor Placement Results**
- Adjust coverage profile
- Modify îlot dimensions
- Check restricted zone configuration

### Debug Mode
```bash
export FLASK_DEBUG=1
python app.py
```

## 📈 Performance

### Optimization Tips
- Use DXF format for fastest processing
- Minimize file size by removing unnecessary layers
- Use appropriate coverage profiles for your space
- Configure layer names accurately

### System Requirements
- **RAM**: 4GB minimum, 8GB recommended
- **CPU**: Multi-core processor recommended
- **Storage**: 1GB free space for processing
- **Network**: Required for web interface

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- **ezdxf**: Excellent DXF/DWG parsing library
- **Shapely**: Powerful geometric operations
- **Flask**: Lightweight web framework
- **OpenCV**: Computer vision capabilities
- **NetworkX**: Graph algorithms implementation

## 📞 Support

For technical support or feature requests:
- Create an issue on GitHub
- Check the documentation in `/templates/about.html`
- Review the API documentation

---

**Floorplan Genie** - Transforming CAD files into intelligent, professional floor plans with advanced architectural algorithms.