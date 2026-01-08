#!/usr/bin/env python3
"""
Example usage of the find_blocks function with the BlueMap connector.

This script demonstrates how to:
1. Connect to a BlueMap instance
2. Parse PRBM tiles to extract block positions
3. Convert tile coordinates to world coordinates
4. Find all blocks in a tile
"""

from connector import BlueMapConnector


def example_find_blocks_in_tile():
    """Example: Find all blocks in a specific tile."""
    print("=== Example: Find Blocks in a Tile ===\n")
    
    # Connect to your BlueMap server
    # Replace with your actual BlueMap URL
    connector = BlueMapConnector("http://localhost:8100")
    
    print("This example would:")
    print("1. Connect to the BlueMap server")
    print("2. Download a PRBM tile at coordinates (0, 0)")
    print("3. Parse the tile to extract all vertex positions")
    print("4. Convert positions to unique block coordinates")
    print("5. Return blocks in in-game world coordinates")
    print()
    
    # Example code (requires real server):
    print("Example code:")
    print("""
    result = connector.find_blocks(
        map_id='world',
        tile_x=0,
        tile_z=0,
        grid_size=16  # Default BlueMap tile size
    )
    
    print(f"Tile bounds: {result['world_bounds']}")
    print(f"Found {len(result['block_positions'])} unique blocks")
    print(f"Number of triangles: {result['num_triangles']}")
    
    # Print first 10 block positions
    for x, y, z in result['block_positions'][:10]:
        print(f"  Block at ({x}, {y}, {z})")
    """)
    print()


def example_coordinate_conversion():
    """Example: Convert between tile and world coordinates."""
    print("=== Example: Coordinate Conversion ===\n")
    
    connector = BlueMapConnector("http://localhost:8100")
    
    # Convert tile coordinates to world bounds
    tile_x, tile_z = 0, 0
    bounds = connector.tile_to_world_coordinates(tile_x, tile_z)
    
    print(f"Tile ({tile_x}, {tile_z}) covers world coordinates:")
    print(f"  From ({bounds[0][0]}, {bounds[0][1]}) "
          f"to ({bounds[1][0]}, {bounds[1][1]})")
    print()
    
    # Convert world coordinates to tile
    world_x, world_z = 100, 200
    tile = connector.world_to_tile_coordinates(world_x, world_z)
    
    print(f"World position ({world_x}, {world_z}) is in tile {tile}")
    print()


def example_scan_area():
    """Example: Scan multiple tiles in an area."""
    print("=== Example: Scan Multiple Tiles ===\n")
    
    print("To scan an area and find all blocks:")
    print("""
    connector = BlueMapConnector("http://localhost:8100")
    
    # Define area to scan
    center_tile_x, center_tile_z = 0, 0
    radius = 2  # Scan 5x5 tiles
    
    all_blocks = []
    
    for tile_x in range(center_tile_x - radius, center_tile_x + radius + 1):
        for tile_z in range(center_tile_z - radius, center_tile_z + radius + 1):
            try:
                result = connector.find_blocks('world', tile_x, tile_z)
                blocks = result['block_positions']
                all_blocks.extend(blocks)
                print(f"Tile ({tile_x}, {tile_z}): {len(blocks)} blocks")
            except Exception as e:
                print(f"Tile ({tile_x}, {tile_z}): Not available")
    
    print(f"\\nTotal unique blocks found: {len(set(all_blocks))}")
    """)
    print()


def example_filter_blocks_by_height():
    """Example: Filter blocks by Y coordinate (height)."""
    print("=== Example: Filter Blocks by Height ===\n")
    
    print("To find blocks at specific heights:")
    print("""
    result = connector.find_blocks('world', tile_x=0, tile_z=0)
    
    # Find all blocks above sea level (y >= 64)
    surface_blocks = [
        (x, y, z) for x, y, z in result['block_positions'] 
        if y >= 64
    ]
    
    # Find all blocks in a specific height range
    cave_blocks = [
        (x, y, z) for x, y, z in result['block_positions']
        if 0 <= y < 64
    ]
    
    print(f"Surface blocks (y >= 64): {len(surface_blocks)}")
    print(f"Underground blocks (0 <= y < 64): {len(cave_blocks)}")
    """)
    print()


def example_get_block_colors():
    """Example: Get block colors from the tile."""
    print("=== Example: Get Block Colors ===\n")
    
    print("To access color information for blocks:")
    print("""
    result = connector.find_blocks('world', tile_x=0, tile_z=0)
    
    # Colors are per-vertex, corresponding to vertex_positions
    if result['colors']:
        print(f"Found {len(result['colors'])} vertex colors")
        
        # First few colors
        for i, (r, g, b) in enumerate(result['colors'][:5]):
            pos = result['vertex_positions'][i]
            print(f"  Vertex at {pos}: RGB({r:.2f}, {g:.2f}, {b:.2f})")
    """)
    print()


def example_parse_prbm_directly():
    """Example: Parse a PRBM file directly."""
    print("=== Example: Parse PRBM File Directly ===\n")
    
    print("To parse a PRBM file you already have:")
    print("""
    connector = BlueMapConnector("http://localhost:8100")
    
    # If you have a PRBM file locally
    with open('tile.prbm', 'rb') as f:
        prbm_data = f.read()
    
    # Parse it
    parsed = connector.parse_prbm_tile(prbm_data)
    
    print(f"Version: {parsed['version']}")
    print(f"Triangles: {parsed['num_triangles']}")
    print(f"Vertices: {parsed['num_values']}")
    
    # Access raw attribute data
    if 'position' in parsed:
        print(f"Position data: {len(parsed['position'])} floats")
    
    # Access parsed positions as tuples
    if 'positions' in parsed:
        print(f"First position: {parsed['positions'][0]}")
    """)
    print()


def main():
    """Run all examples."""
    print("BlueMap Connector - PRBM Parser Examples")
    print("=" * 60)
    print()
    
    example_find_blocks_in_tile()
    example_coordinate_conversion()
    example_scan_area()
    example_filter_blocks_by_height()
    example_get_block_colors()
    example_parse_prbm_directly()
    
    print("=" * 60)
    print("\nNote: These examples show the API usage.")
    print("To run them with a real server, update the URL and ensure")
    print("the BlueMap instance is accessible.")


if __name__ == "__main__":
    main()
