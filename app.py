# Main production app - redirect to enhanced version
from enhanced_production_app import app

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5000)