import os
import sys
from pathlib import Path

project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from parsers.dwg_dxf_parser import parse_dwg_dxf
from parsers.pdf_parser import parse_pdf
from geometry_processor import process_geometry
from layout_optimizer_fast import optimize_layout
from visualizer import visualize_plan

class FastFloorPlanEngine:
    def __init__(self):
        self.supported_formats = {'.dxf', '.dwg', '.pdf'}
        self.coverage_profiles = {
            'low': 0.10, 'medium': 0.25, 'high': 0.30, 'maximum': 0.35
        }
    
    def generate_floorplan(self, input_path, output_path, islands_str="", corridor_width=1.2, 
                          wall_layer="0", prohibited_layer="PROHIBITED", entrance_layer="ENTRANCE",
                          coverage_profile="medium"):
        """Fast floor plan generation"""
        print("=== FAST FLOORPLAN GENIE ===")
        print(f"Processing: {Path(input_path).name}")
        
        if not self._validate_input(input_path):
            return None
        
        # Fast parsing
        classified_entities = self._parse_file(input_path)
        if not classified_entities:
            print("ERROR: Parse failed")
            return None
        
        # Fast geometry processing
        processed_geometry = self._process_geometry(
            classified_entities, wall_layer, prohibited_layer, entrance_layer
        )
        if not processed_geometry:
            print("ERROR: Geometry failed")
            return None
        
        # Fast layout optimization
        island_dimensions = self._parse_island_dimensions(islands_str)
        coverage = self.coverage_profiles.get(coverage_profile, 0.25)
        
        optimized_layout = self._optimize_layout(
            processed_geometry, island_dimensions, corridor_width, coverage
        )
        
        # Fast visualization
        result_path = self._create_visualization(
            processed_geometry, optimized_layout, output_path
        )
        
        self._print_summary(processed_geometry, optimized_layout)
        return result_path
    
    def _validate_input(self, input_path):
        if not os.path.exists(input_path):
            print(f"ERROR: File not found: {input_path}")
            return False
        
        file_ext = Path(input_path).suffix.lower()
        if file_ext not in self.supported_formats:
            print(f"ERROR: Unsupported format: {file_ext}")
            return False
        
        return True
    
    def _parse_file(self, input_path):
        file_ext = Path(input_path).suffix.lower()
        print(f"Parsing {file_ext.upper()}...")
        
        try:
            if file_ext in ['.dxf', '.dwg']:
                return parse_dwg_dxf(input_path)
            elif file_ext == '.pdf':
                return parse_pdf(input_path)
        except Exception as e:
            print(f"Parse error: {e}")
            return None
    
    def _process_geometry(self, classified_entities, wall_layer, prohibited_layer, entrance_layer):
        print("Processing geometry...")
        try:
            return process_geometry(classified_entities, wall_layer, prohibited_layer, entrance_layer)
        except Exception as e:
            print(f"Geometry error: {e}")
            return None
    
    def _optimize_layout(self, geometry, island_dimensions, corridor_width, coverage):
        print("Optimizing layout...")
        try:
            usable_area = geometry.get('usable_area')
            if not usable_area or usable_area.is_empty:
                print("WARNING: No usable area")
                return {"islands": [], "corridors": [], "stats": {}}
            
            return optimize_layout(usable_area, island_dimensions, corridor_width)
        except Exception as e:
            print(f"Layout error: {e}")
            return {"islands": [], "corridors": [], "stats": {}}
    
    def _create_visualization(self, geometry, layout, output_path):
        print("Creating visualization...")
        try:
            output_dir = Path(output_path).parent
            output_dir.mkdir(parents=True, exist_ok=True)
            return visualize_plan(geometry, layout, output_path)
        except Exception as e:
            print(f"Visualization error: {e}")
            return None
    
    def _parse_island_dimensions(self, dims_string):
        if not dims_string:
            return [(3, 2), (4, 3), (2, 2)]  # Simplified defaults
        
        dimensions = []
        try:
            for part in dims_string.split(','):
                w, h = part.strip().split('x')
                dimensions.append((float(w), float(h)))
        except:
            print("Invalid dimensions, using defaults")
            return [(3, 2), (4, 3), (2, 2)]
        
        return dimensions
    
    def _print_summary(self, geometry, layout):
        print("\n=== SUMMARY ===")
        if geometry:
            print(f"Total Area: {geometry.get('total_area', 0):.1f}m²")
        
        stats = layout.get('stats', {})
        if stats:
            print(f"Islands: {stats.get('islands_placed', 0)}")
            print(f"Coverage: {stats.get('island_coverage', 0)*100:.1f}%")
        print("=== COMPLETE ===\n")

# Global fast engine
_fast_engine = FastFloorPlanEngine()

def generate_floorplan(input_path, output_path, islands_str="", corridor_width=1.2,
                      wall_layer="0", prohibited_layer="PROHIBITED", entrance_layer="ENTRANCE"):
    """Fast generation function"""
    return _fast_engine.generate_floorplan(
        input_path, output_path, islands_str, corridor_width,
        wall_layer, prohibited_layer, entrance_layer
    )