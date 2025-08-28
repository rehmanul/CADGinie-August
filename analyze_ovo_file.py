#!/usr/bin/env python3

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from production_engine import generate_production_floorplan

def analyze_ovo_dxf():
    """Analyze the specific OVO DOSSIER COSTO DXF file"""
    
    input_file = r"C:\Users\HP\Desktop\FLOORPLAN_GENIE\input_files\ovo DOSSIER COSTO - plan rdc rdj - cota.dxf"
    output_file = r"C:\Users\HP\Desktop\FLOORPLAN_GENIE\output_files\ovo_analysis_result.png"
    
    print("🏗️ ANALYZING OVO DOSSIER COSTO FLOOR PLAN")
    print("=" * 60)
    print(f"Input: {Path(input_file).name}")
    print(f"Size: {os.path.getsize(input_file) / (1024*1024):.1f}MB")
    print("=" * 60)
    
    # Generate with professional settings
    result = generate_production_floorplan(
        input_path=input_file,
        output_path=output_file,
        islands_str="3x2,4x3,5x4,2x2,3x3,4x4",  # Professional îlot mix
        corridor_width=1.2,  # Standard corridor width
        wall_layer="0",  # Common wall layer
        prohibited_layer="PROHIBITED",
        entrance_layer="ENTRANCE", 
        coverage_profile="medium",  # 25% coverage
        title="OVO DOSSIER COSTO - Professional Analysis"
    )
    
    if result:
        print(f"\n✅ SUCCESS: Analysis complete!")
        print(f"📊 Visual output: {result}")
        print(f"📁 File size: {os.path.getsize(result) / 1024:.1f}KB")
        return result
    else:
        print("\n❌ FAILED: Analysis could not be completed")
        return None

if __name__ == "__main__":
    analyze_ovo_dxf()