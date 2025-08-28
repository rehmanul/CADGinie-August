# main.py
# This script orchestrates the entire floor plan generation process.

import argparse
import os
import sys

# Ensure the script can find the custom modules
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from parsers import dwg_dxf_parser, pdf_parser
from geometry_processor import process_geometry
from layout_optimizer import optimize_layout
from visualizer import visualize_plan

def parse_island_dimensions(dims_string):
    """Parses the island dimensions string (e.g., "10x20,5x15") into a list of tuples."""
    dimensions = []
    if not dims_string:
        return []
    try:
        parts = dims_string.split(',')
        for part in parts:
            w, h = part.strip().split('x')
            dimensions.append((float(w), float(h)))
    except ValueError:
        print(f"Error: Invalid island dimensions format: '{dims_string}'. Use format like '10x20,5x15'.")
        sys.exit(1)
    return dimensions

def main():
    """Main function to run the floor plan generation process."""
    parser = argparse.ArgumentParser(description="Automated Floor Plan Layout Generator")
    parser.add_argument("--input", required=True, help="Path to the input floor plan file (DWG, DXF, or PDF).")
    parser.add_argument("--output", required=True, help="Path to save the output image (e.g., 'output/plan.png').")
    parser.add_argument("--islands", required=True, help="Comma-separated list of island dimensions (e.g., '10x20,5x15').")
    parser.add_argument("--corridor-width", type=float, default=1.2, help="Width of the corridors (default: 1.2).")
    
    # Optional arguments for layer names in CAD files
    parser.add_argument("--wall-layer", default="WALLS", help="Layer name for walls.")
    parser.add_argument("--prohibited-layer", default="PROHIBITED", help="Layer name for prohibited areas.")
    parser.add_argument("--entrance-layer", default="ENTRANCE", help="Layer name for entrance/exit areas.")

    args = parser.parse_args()

    # --- 1. File Parsing ---
    if not os.path.exists(args.input):
        print(f"Error: Input file not found at '{args.input}'")
        sys.exit(1)

    file_ext = os.path.splitext(args.input)[1].lower()
    raw_entities = None

    if file_ext in ['.dxf', '.dwg']:
        raw_entities = dwg_dxf_parser.parse_dwg_dxf(args.input)
    elif file_ext == '.pdf':
        raw_entities = pdf_parser.parse_pdf(args.input)
    else:
        print(f"Error: Unsupported file type '{file_ext}'. Please use DWG, DXF, or PDF.")
        sys.exit(1)

    if not raw_entities:
        print("Error: No geometric entities were extracted from the input file.")
        sys.exit(1)

    # --- 2. Geometry Processing ---
    print("\n--- Starting Geometry Processing ---")
    processed_geometry = process_geometry(
        raw_entities,
        wall_layer=args.wall_layer,
        prohibited_layer=args.prohibited_layer,
        entrance_layer=args.entrance_layer
    )

    if not processed_geometry or not processed_geometry.get("usable_area"):
        print("Error: Failed to process geometry or define a usable area.")
        sys.exit(1)

    # --- 3. Layout Optimization ---
    print("\n--- Starting Layout Optimization ---")
    island_dims = parse_island_dimensions(args.islands)
    final_layout = optimize_layout(
        processed_geometry["usable_area"],
        island_dims,
        args.corridor_width
    )

    # --- 4. Visualization ---
    print("\n--- Starting Visualization ---")
    output_dir = os.path.dirname(args.output)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    visualize_plan(
        processed_geometry,
        final_layout,
        args.output
    )

    print("\nProcess finished successfully!")
    print(f"Final layout image saved to: {args.output}")

if __name__ == "__main__":
    main()
