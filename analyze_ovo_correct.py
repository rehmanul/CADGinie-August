#!/usr/bin/env python3

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from production_engine import generate_production_floorplan

def analyze_ovo_with_correct_layers():
    """Analyze OVO DXF with correct layer configuration"""
    
    input_file = r"C:\Users\HP\Desktop\FLOORPLAN_GENIE\input_files\ovo DOSSIER COSTO - plan rdc rdj - cota.dxf"
    output_file = r"C:\Users\HP\Desktop\FLOORPLAN_GENIE\output_files\ovo_professional_analysis.png"
    
    print("🏗️ OVO DOSSIER COSTO - PROFESSIONAL ANALYSIS")
    print("=" * 60)
    print(f"📁 Input: {Path(input_file).name}")
    print(f"📊 Size: {os.path.getsize(input_file) / (1024*1024):.1f}MB")
    print(f"🎯 Layers: P (walls), H (areas)")
    print("=" * 60)
    
    # Generate with correct layer configuration
    result = generate_production_floorplan(
        input_path=input_file,
        output_path=output_file,
        islands_str="3x2,4x2,5x3,3x3,4x4,2x2",  # Professional îlot sizes
        corridor_width=1.2,  # Standard 1.2m corridors
        wall_layer="P",  # LWPOLYLINE layer for walls
        prohibited_layer="H",  # HATCH layer for restricted areas
        entrance_layer="0",  # Default layer for entrances
        coverage_profile="medium",  # 25% coverage
        title="OVO DOSSIER COSTO - RDC/RDJ Professional Floor Plan"
    )
    
    if result:
        print(f"\n✅ SUCCESS: Professional analysis complete!")
        print(f"🖼️  Visual output: {result}")
        print(f"📏 File size: {os.path.getsize(result) / 1024:.1f}KB")
        
        # Show what the user will see
        print(f"\n🎨 VISUAL OUTPUT PREVIEW:")
        print(f"   • Walls (gray): Structural boundaries from layer P")
        print(f"   • Restricted areas (blue): Hatched zones from layer H") 
        print(f"   • Îlots (green): Intelligently placed furniture islands")
        print(f"   • Corridors (pink): 1.2m wide circulation paths")
        print(f"   • Measurements: Area calculations and dimensions")
        print(f"   • Legend: Professional color-coded elements")
        
        return result
    else:
        print("\n❌ FAILED: Analysis could not be completed")
        return None

if __name__ == "__main__":
    analyze_ovo_with_correct_layers()