import os
import uuid
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file
from werkzeug.utils import secure_filename
from pathlib import Path
from production_engine import ProductionFloorPlanEngine

UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'static'
ALLOWED_EXTENSIONS = {'dxf', 'pdf', 'dwg'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 64 * 1024 * 1024
app.secret_key = 'production_floorplan_genie_2024'

Path(UPLOAD_FOLDER).mkdir(exist_ok=True)
Path(OUTPUT_FOLDER).mkdir(exist_ok=True)

engine = ProductionFloorPlanEngine()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        flash('No file selected')
        return redirect(url_for('index'))

    file = request.files['file']
    if file.filename == '' or not (file and allowed_file(file.filename)):
        flash('Invalid file. Please upload DXF, DWG, or PDF files.')
        return redirect(url_for('index'))

    try:
        filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4().hex}_{filename}"
        input_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(input_path)

        islands_str = request.form.get('islands', '2x2,3x2,4x2,3x3,4x3,5x3,4x4,5x4')
        corridor_width = float(request.form.get('corridor_width', 1.2))
        wall_layer = request.form.get('wall_layer', '0')
        prohibited_layer = request.form.get('prohibited_layer', 'PROHIBITED')
        entrance_layer = request.form.get('entrance_layer', 'ENTRANCE')
        coverage_profile = request.form.get('coverage_profile', 'medium')
        
        if not (0.8 <= corridor_width <= 3.0):
            corridor_width = 1.2
            flash('Corridor width adjusted to 1.2m (valid range: 0.8-3.0m)')

        output_filename = f"production_{uuid.uuid4().hex}.png"
        output_path = os.path.join(app.config['OUTPUT_FOLDER'], output_filename)

        result_path = engine.generate_production_floorplan(
            input_path=input_path,
            output_path=output_path,
            islands_str=islands_str,
            corridor_width=corridor_width,
            wall_layer=wall_layer,
            prohibited_layer=prohibited_layer,
            entrance_layer=entrance_layer,
            coverage_profile=coverage_profile,
            title=f"Professional Floor Plan - {Path(filename).stem}"
        )

        try:
            os.remove(input_path)
        except:
            pass

        if result_path and os.path.exists(result_path):
            return render_template('results.html', 
                                 image_filename=output_filename,
                                 success=True,
                                 original_filename=filename)
        else:
            flash('Processing failed. Please check your file format and layer names.')
            return redirect(url_for('index'))

    except Exception as e:
        flash(f'Processing error: {str(e)}')
        try:
            if 'input_path' in locals():
                os.remove(input_path)
        except:
            pass
        return redirect(url_for('index'))

@app.route('/api/process', methods=['POST'])
def api_process():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided', 'success': False}), 400

        file = request.files['file']
        if not (file and allowed_file(file.filename)):
            return jsonify({'error': 'Invalid file type. Use DXF, DWG, or PDF.', 'success': False}), 400

        filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4().hex}_{filename}"
        input_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(input_path)

        params = request.form.to_dict()
        islands_str = params.get('islands', '2x2,3x2,4x2,3x3,4x3,5x3,4x4,5x4')
        corridor_width = float(params.get('corridor_width', 1.2))
        wall_layer = params.get('wall_layer', '0')
        prohibited_layer = params.get('prohibited_layer', 'PROHIBITED')
        entrance_layer = params.get('entrance_layer', 'ENTRANCE')
        coverage_profile = params.get('coverage_profile', 'medium')
        
        if not (0.8 <= corridor_width <= 3.0):
            corridor_width = 1.2
        
        if coverage_profile not in ['low', 'medium', 'high', 'maximum']:
            coverage_profile = 'medium'

        output_filename = f"api_production_{uuid.uuid4().hex}.png"
        output_path = os.path.join(app.config['OUTPUT_FOLDER'], output_filename)

        result_path = engine.generate_production_floorplan(
            input_path=input_path,
            output_path=output_path,
            islands_str=islands_str,
            corridor_width=corridor_width,
            wall_layer=wall_layer,
            prohibited_layer=prohibited_layer,
            entrance_layer=entrance_layer,
            coverage_profile=coverage_profile,
            title=f"API Generated Plan - {Path(filename).stem}"
        )

        try:
            os.remove(input_path)
        except:
            pass

        if result_path and os.path.exists(result_path):
            file_size = os.path.getsize(result_path)
            return jsonify({
                'success': True,
                'message': 'Floor plan generated successfully',
                'result_url': url_for('static', filename=output_filename),
                'download_url': url_for('download_result', filename=output_filename),
                'file_size': file_size,
                'original_filename': filename
            })
        else:
            return jsonify({'error': 'Processing failed. Check file format and parameters.', 'success': False}), 500

    except Exception as e:
        try:
            if 'input_path' in locals():
                os.remove(input_path)
        except:
            pass
        
        return jsonify({'error': f'Processing error: {str(e)}', 'success': False}), 500

@app.route('/download/<filename>')
def download_result(filename):
    try:
        file_path = os.path.join(app.config['OUTPUT_FOLDER'], filename)
        if os.path.exists(file_path):
            return send_file(file_path, 
                           as_attachment=True, 
                           download_name=f"floorplan_production_{filename}",
                           mimetype='image/png')
        else:
            flash('File not found or expired')
            return redirect(url_for('index'))
    except Exception as e:
        flash(f'Download error: {str(e)}')
        return redirect(url_for('index'))

@app.route('/gallery')
def gallery():
    try:
        output_dir = Path(app.config['OUTPUT_FOLDER'])
        image_files = []
        
        for file_path in output_dir.glob('*.png'):
            if file_path.is_file():
                file_info = {
                    'name': file_path.name,
                    'size': file_path.stat().st_size,
                    'created': file_path.stat().st_ctime,
                    'url': url_for('static', filename=file_path.name)
                }
                image_files.append(file_info)
        
        image_files.sort(key=lambda x: x['created'], reverse=True)
        
        return render_template('gallery.html', images=image_files[:20])
    except Exception as e:
        flash(f'Gallery error: {str(e)}')
        return redirect(url_for('index'))

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/api/status')
def api_status():
    return jsonify({
        'status': 'operational',
        'version': '2.0.0',
        'engine': 'production',
        'supported_formats': list(ALLOWED_EXTENSIONS),
        'max_file_size': '64MB',
        'features': [
            'Multi-sheet CAD parsing',
            'Architectural element classification',
            'Intelligent îlot placement',
            'Corridor network generation',
            'Pixel-perfect rendering',
            'Professional styling'
        ]
    })

@app.errorhandler(413)
def too_large(e):
    flash('File too large. Maximum size is 64MB.')
    return redirect(url_for('index'))

@app.errorhandler(404)
def not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def server_error(e):
    return render_template('500.html'), 500

if __name__ == '__main__':
    print("=" * 60)
    print("FLOORPLAN GENIE - PRODUCTION ENGINE")
    print("=" * 60)
    print("Advanced CAD Processing & Intelligent Layout Generation")
    print("")
    print("Features:")
    print("  ✓ Multi-sheet DXF/DWG/PDF parsing")
    print("  ✓ Architectural element classification")
    print("  ✓ Intelligent îlot placement (10%-35% coverage)")
    print("  ✓ Mandatory corridor network generation")
    print("  ✓ Pixel-perfect professional rendering")
    print("  ✓ Interactive legend and measurements")
    print("  ✓ High-resolution export (300 DPI)")
    print("")
    print("Access Points:")
    print(f"  Web Interface: http://localhost:5000")
    print(f"  API Endpoint:  http://localhost:5000/api/process")
    print(f"  API Status:    http://localhost:5000/api/status")
    print("=" * 60)
    
    app.run(debug=False, host='0.0.0.0', port=5000, threaded=True)