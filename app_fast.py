import os
import uuid
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file
from werkzeug.utils import secure_filename
from pathlib import Path
from core_logic_fast import FastFloorPlanEngine

# Fast App Configuration
UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'static'
ALLOWED_EXTENSIONS = {'dxf', 'pdf', 'dwg'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 32 * 1024 * 1024  # Reduced to 32MB for speed
app.secret_key = 'fast_floorplan_genie'

Path(UPLOAD_FOLDER).mkdir(exist_ok=True)
Path(OUTPUT_FOLDER).mkdir(exist_ok=True)

# Fast engine
engine = FastFloorPlanEngine()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    """Fast file processing"""
    if 'file' not in request.files:
        flash('No file selected')
        return redirect(url_for('index'))

    file = request.files['file']
    if file.filename == '' or not (file and allowed_file(file.filename)):
        flash('Invalid file. Use DXF, DWG, or PDF.')
        return redirect(url_for('index'))

    try:
        # Save file
        filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4().hex[:8]}_{filename}"  # Shorter UUID
        input_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(input_path)

        # Get parameters (simplified)
        islands_str = request.form.get('islands', '3x2,4x3,2x2')
        corridor_width = float(request.form.get('corridor_width', 1.2))
        wall_layer = request.form.get('wall_layer', '0')
        prohibited_layer = request.form.get('prohibited_layer', 'PROHIBITED')
        entrance_layer = request.form.get('entrance_layer', 'ENTRANCE')
        coverage_profile = request.form.get('coverage_profile', 'medium')

        # Generate output
        output_filename = f"result_{uuid.uuid4().hex[:8]}.png"  # Shorter UUID
        output_path = os.path.join(app.config['OUTPUT_FOLDER'], output_filename)

        # Fast processing
        result_path = engine.generate_floorplan(
            input_path=input_path,
            output_path=output_path,
            islands_str=islands_str,
            corridor_width=corridor_width,
            wall_layer=wall_layer,
            prohibited_layer=prohibited_layer,
            entrance_layer=entrance_layer,
            coverage_profile=coverage_profile
        )

        # Cleanup
        try:
            os.remove(input_path)
        except:
            pass

        if result_path and os.path.exists(result_path):
            return render_template('results.html', 
                                 image_filename=output_filename,
                                 success=True)
        else:
            flash('Processing failed. Check file and try again.')
            return redirect(url_for('index'))

    except Exception as e:
        flash(f'Error: {str(e)}')
        return redirect(url_for('index'))

@app.route('/gallery')
def gallery():
    """Fast gallery"""
    try:
        output_dir = Path(app.config['OUTPUT_FOLDER'])
        image_files = [f.name for f in output_dir.glob('*.png') if f.is_file()]
        image_files.sort(reverse=True)
        return render_template('gallery.html', images=image_files[:10])  # Show last 10
    except Exception as e:
        flash(f'Gallery error: {str(e)}')
        return redirect(url_for('index'))

@app.route('/about')
def about():
    return render_template('about.html')

@app.errorhandler(413)
def too_large(e):
    flash('File too large. Max 32MB.')
    return redirect(url_for('index'))

if __name__ == '__main__':
    print("=== FAST FLOORPLAN GENIE ===")
    print("Optimized for speed and performance")
    print("Access: http://localhost:5000")
    app.run(debug=False, host='0.0.0.0', port=5000, threaded=True)