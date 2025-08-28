#!/usr/bin/env python3

from flask import Flask, request, jsonify, render_template, send_file, url_for
from werkzeug.utils import secure_filename
import os
import uuid
import json
from datetime import datetime
import logging
from production_engine import ProductionFloorPlanEngine
from advanced_cad_processor import AdvancedCADProcessor
from intelligent_layout_optimizer import IntelligentLayoutOptimizer
from pixel_perfect_renderer import PixelPerfectRenderer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'production-floorplan-genie-2024')
app.config['MAX_CONTENT_LENGTH'] = 64 * 1024 * 1024  # 64MB max file size

# Production directories
UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'output_files'
STATIC_FOLDER = 'static'

for folder in [UPLOAD_FOLDER, OUTPUT_FOLDER, STATIC_FOLDER]:
    os.makedirs(folder, exist_ok=True)

# Initialize production engines
cad_processor = AdvancedCADProcessor()
layout_optimizer = IntelligentLayoutOptimizer()
renderer = PixelPerfectRenderer()
engine = ProductionFloorPlanEngine(cad_processor, layout_optimizer, renderer)

@app.route('/')
def index():
    """Main application interface"""
    return render_template('production_index.html')

@app.route('/api/upload', methods=['POST'])
def upload_file():
    """Handle file upload with validation"""
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file provided'})
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'})
        
        # Validate file type
        allowed_extensions = {'.dxf', '.dwg', '.pdf'}
        file_ext = os.path.splitext(file.filename)[1].lower()
        
        if file_ext not in allowed_extensions:
            return jsonify({'success': False, 'error': f'Unsupported file type: {file_ext}'})
        
        # Generate unique filename
        file_id = str(uuid.uuid4())
        filename = f"{file_id}{file_ext}"
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        
        # Save file
        file.save(filepath)
        
        logger.info(f"File uploaded: {filename} ({os.path.getsize(filepath)} bytes)")
        
        return jsonify({
            'success': True,
            'file_id': file_id,
            'filename': file.filename,
            'size': os.path.getsize(filepath)
        })
        
    except Exception as e:
        logger.error(f"Upload error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/process', methods=['POST'])
def process_floorplan():
    """Process floor plan with full production pipeline"""
    try:
        data = request.get_json()
        
        # Validate required parameters
        required_params = ['file_id', 'islands', 'corridor_width', 'coverage_profile']
        for param in required_params:
            if param not in data:
                return jsonify({'success': False, 'error': f'Missing parameter: {param}'})
        
        file_id = data['file_id']
        
        # Find uploaded file
        uploaded_file = None
        for ext in ['.dxf', '.dwg', '.pdf']:
            filepath = os.path.join(UPLOAD_FOLDER, f"{file_id}{ext}")
            if os.path.exists(filepath):
                uploaded_file = filepath
                break
        
        if not uploaded_file:
            return jsonify({'success': False, 'error': 'File not found'})
        
        # Process with production engine
        result = engine.process_complete_floorplan(
            file_path=uploaded_file,
            islands=data['islands'],
            corridor_width=float(data['corridor_width']),
            coverage_profile=data['coverage_profile'],
            wall_layer=data.get('wall_layer', '0'),
            prohibited_layer=data.get('prohibited_layer', 'PROHIBITED'),
            entrance_layer=data.get('entrance_layer', 'DOORS')
        )
        
        if result['success']:
            # Generate output filename
            output_id = str(uuid.uuid4())
            output_filename = f"floorplan_{output_id}.png"
            output_path = os.path.join(OUTPUT_FOLDER, output_filename)
            
            # Render final result
            renderer.render_production_floorplan(
                result['geometry'],
                result['layout'],
                output_path,
                title=f"Professional Floor Plan - {datetime.now().strftime('%Y-%m-%d')}"
            )
            
            logger.info(f"Floor plan processed successfully: {output_filename}")
            
            return jsonify({
                'success': True,
                'result_id': output_id,
                'result_url': url_for('get_result', result_id=output_id),
                'download_url': url_for('download_result', result_id=output_id),
                'statistics': result['statistics'],
                'processing_time': result['processing_time']
            })
        else:
            return jsonify({'success': False, 'error': result['error']})
            
    except Exception as e:
        logger.error(f"Processing error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/result/<result_id>')
def get_result(result_id):
    """Get processing result"""
    try:
        result_path = os.path.join(OUTPUT_FOLDER, f"floorplan_{result_id}.png")
        
        if not os.path.exists(result_path):
            return jsonify({'success': False, 'error': 'Result not found'})
        
        return jsonify({
            'success': True,
            'image_url': url_for('static', filename=f'../output_files/floorplan_{result_id}.png'),
            'created': datetime.fromtimestamp(os.path.getctime(result_path)).isoformat(),
            'size': os.path.getsize(result_path)
        })
        
    except Exception as e:
        logger.error(f"Result retrieval error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/download/<result_id>')
def download_result(result_id):
    """Download result file"""
    try:
        result_path = os.path.join(OUTPUT_FOLDER, f"floorplan_{result_id}.png")
        
        if not os.path.exists(result_path):
            return jsonify({'success': False, 'error': 'File not found'}), 404
        
        return send_file(
            result_path,
            as_attachment=True,
            download_name=f"professional_floorplan_{result_id}.png",
            mimetype='image/png'
        )
        
    except Exception as e:
        logger.error(f"Download error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/health')
def health_check():
    """Health check endpoint for deployment"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0',
        'engines': {
            'cad_processor': 'ready',
            'layout_optimizer': 'ready',
            'renderer': 'ready'
        }
    })

@app.route('/api/capabilities')
def get_capabilities():
    """Get system capabilities"""
    return jsonify({
        'supported_formats': ['DXF', 'DWG', 'PDF'],
        'max_file_size': '64MB',
        'coverage_profiles': ['10%', '25%', '30%', '35%'],
        'corridor_widths': {'min': 0.8, 'max': 3.0, 'default': 1.2},
        'output_formats': ['PNG', 'SVG', 'PDF'],
        'features': [
            'Multi-sheet CAD processing',
            'Layer-aware extraction',
            'Intelligent îlot placement',
            'Corridor network generation',
            'Pixel-perfect rendering',
            'Interactive visualization',
            'Export capabilities'
        ]
    })

@app.errorhandler(413)
def file_too_large(error):
    """Handle file size limit exceeded"""
    return jsonify({'success': False, 'error': 'File too large (max 64MB)'}), 413

@app.errorhandler(500)
def internal_error(error):
    """Handle internal server errors"""
    logger.error(f"Internal server error: {str(error)}")
    return jsonify({'success': False, 'error': 'Internal server error'}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    
    logger.info(f"Starting Floorplan Genie Production Server on port {port}")
    app.run(host='0.0.0.0', port=port, debug=debug)