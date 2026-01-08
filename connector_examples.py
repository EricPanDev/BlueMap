#!/usr/bin/env python3
"""
Example script demonstrating BlueMap connector usage.

This script shows various ways to interact with a BlueMap instance.
"""

from connector import BlueMapConnector


def example_basic_connection():
    """Example: Basic connection and fetching settings."""
    print("=== Example 1: Basic Connection ===\n")
    
    # Create connector
    connector = BlueMapConnector("http://localhost:8100")
    
    # This would fail without a real server, but shows the API
    print("Connector created for: http://localhost:8100")
    print("Call connector.get_settings() to fetch settings")
    print("Call connector.get_maps() to get available maps")
    print()


def example_tile_operations():
    """Example: Working with tiles."""
    print("=== Example 2: Tile Operations ===\n")
    
    connector = BlueMapConnector("http://example-server.com:8100")
    
    # Path demonstration (doesn't require network)
    path = connector._path_from_coords(123, -45)
    print(f"Tile path for (123, -45): {path}")
    
    path = connector._path_from_coords(0, 0)
    print(f"Tile path for (0, 0): {path}")
    
    # Show URL construction concept
    print("\nTo get tile URLs:")
    print("  tile_url = connector.get_tile_url('world', x=0, z=0, lod=0)")
    print("  # Returns: http://example-server.com:8100/maps/world/tiles/0/x0/z0.prbm")
    print()
    print("  tile_url = connector.get_tile_url('world', x=5, z=-3, lod=1)")
    print("  # Returns: http://example-server.com:8100/maps/world/tiles/1/x5/z-3.png")
    
    print()


def example_search_blocks():
    """Example: Searching for blocks in an area."""
    print("=== Example 3: Block Search ===\n")
    
    connector = BlueMapConnector("http://localhost:8100")
    
    print("To search for blocks:")
    print("  results = connector.search_block(")
    print("      'diamond_ore',")
    print("      map_id='world',")
    print("      center_x=0,")
    print("      center_z=0,")
    print("      radius=10")
    print("  )")
    print()
    print("This will:")
    print("  1. Check tiles in a 21x21 area around (0, 0)")
    print("  2. Return list of (x, z) coordinates for existing tiles")
    print("  3. Print progress during the search")
    print()


def example_area_download():
    """Example: Downloading tiles in an area."""
    print("=== Example 4: Download Tiles in Area ===\n")
    
    connector = BlueMapConnector("http://localhost:8100")
    
    print("To download all tiles in a rectangular area:")
    print("  tiles = connector.get_tiles_in_area(")
    print("      map_id='world',")
    print("      min_x=-5, max_x=5,")
    print("      min_z=-5, max_z=5,")
    print("      lod=0")
    print("  )")
    print()
    print("Returns: List of (x, z, tile_data) tuples")
    print()


def example_check_existence():
    """Example: Checking if tiles exist."""
    print("=== Example 5: Check Tile Existence ===\n")
    
    connector = BlueMapConnector("http://localhost:8100")
    
    print("To check if a tile exists (without downloading):")
    print("  exists = connector.check_tile_exists(")
    print("      map_id='world',")
    print("      x=10,")
    print("      z=20,")
    print("      lod=0")
    print("  )")
    print()
    print("Returns: True if tile exists, False otherwise")
    print("Useful for scanning large areas efficiently")
    print()


def example_real_usage():
    """Example: Real-world usage pattern."""
    print("=== Example 6: Real-World Usage Pattern ===\n")
    
    print("# Connect to your BlueMap server")
    print("connector = BlueMapConnector('http://192.168.1.100:8100')")
    print()
    print("# Get list of maps")
    print("maps = connector.get_maps()")
    print("print(f'Found {len(maps)} maps: {list(maps.keys())}')")
    print()
    print("# Get details for a specific map")
    print("world_settings = connector.get_map_settings('world')")
    print("print(f'World name: {world_settings[\"name\"]}')")
    print("print(f'Start position: {world_settings[\"startPos\"]}')")
    print()
    print("# Search for existing tiles near spawn")
    print("spawn_tiles = connector.search_block(")
    print("    'any',  # block name doesn't matter for existence check")
    print("    map_id='world',")
    print("    center_x=0,")
    print("    center_z=0,")
    print("    radius=3")
    print(")")
    print()
    print("# Download a specific tile")
    print("if spawn_tiles:")
    print("    x, z = spawn_tiles[0]")
    print("    tile_data = connector.get_tile('world', x, z, lod=0)")
    print("    print(f'Downloaded {len(tile_data)} bytes')")
    print()


def main():
    """Run all examples."""
    print("BlueMap Connector - Usage Examples")
    print("=" * 50)
    print()
    
    example_basic_connection()
    example_tile_operations()
    example_search_blocks()
    example_area_download()
    example_check_existence()
    example_real_usage()
    
    print("=" * 50)
    print("\nFor more information, see CONNECTOR_README.md")
    print("To test with a real server:")
    print("  python connector.py http://your-bluemap-url:8100")


if __name__ == "__main__":
    main()
