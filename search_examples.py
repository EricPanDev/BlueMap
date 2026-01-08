#!/usr/bin/env python3
"""
Examples demonstrating how to use search.py to find blocks on a BlueMap server.

This script shows both command-line usage and programmatic usage of the search functions.
"""

from search import search_blocks_in_area, search_blocks_in_radius
from connector import BlueMapConnector


def example_command_line_usage():
    """Show examples of using search.py from the command line."""
    
    print("=" * 70)
    print("search.py - Command Line Examples")
    print("=" * 70)
    print()
    
    print("BLOCK TYPE IDENTIFICATION:")
    print("The search tool can now identify specific block types using textures.json!")
    print("Use --block-type to search for specific blocks like oak logs.")
    print()
    print("=" * 70)
    print()
    
    print("1. Search for ALL blocks in a 5-tile radius around spawn:")
    print("   $ python search.py http://localhost:8100 world --radius 5")
    print()
    
    print("2. Search for OAK LOGS specifically:")
    print("   $ python search.py http://localhost:8100 world --radius 5 --block-type minecraft:block/oak_log")
    print()
    
    print("3. Search for DIAMOND ORE at diamond level:")
    print("   $ python search.py http://localhost:8100 world --radius 10 \\")
    print("           --block-type minecraft:block/diamond_ore --min-y -64 --max-y 16")
    print()
    
    print("4. Search with height filter (surface level):")
    print("   $ python search.py http://localhost:8100 world --radius 3 --min-y 60 --max-y 100")
    
    print("3. Search specific tile range:")
    print("   $ python search.py http://localhost:8100 world --tile-range -2,-2 2,2")
    print()
    
    print("4. Export results to CSV file:")
    print("   $ python search.py http://localhost:8100 world --radius 2 --output blocks.csv")
    print()
    
    print("5. Search underground at diamond level:")
    print("   $ python search.py http://localhost:8100 world --radius 5 --min-y -64 --max-y 16")
    print()
    
    print("6. Limit output to first 100 coordinates:")
    print("   $ python search.py http://localhost:8100 world --radius 1 --limit 100")
    print()
    
    print("7. Quiet mode (only output coordinates, no progress):")
    print("   $ python search.py http://localhost:8100 world --radius 1 --quiet")
    print()


def example_programmatic_usage():
    """Show examples of using the search functions programmatically."""
    
    print()
    print("=" * 70)
    print("Programmatic Usage Examples")
    print("=" * 70)
    print()
    
    print("Example 1: Search and process coordinates")
    print("-" * 70)
    print("""
from search import search_blocks_in_radius
from connector import BlueMapConnector

# Connect to BlueMap server
connector = BlueMapConnector("http://localhost:8100")

# Search for blocks in a 3-tile radius around spawn
# with height filter for surface blocks (where trees grow)
surface_blocks = set()

for x, y, z in search_blocks_in_radius(
    connector, 
    map_id="world",
    center_x=0, 
    center_z=0, 
    radius=3,
    min_y=60,  # Surface level
    max_y=100, # Below clouds
    verbose=True
):
    surface_blocks.add((x, y, z))

print(f"Found {len(surface_blocks)} unique surface block positions")

# Analyze by height
height_counts = {}
for x, y, z in surface_blocks:
    height_counts[y] = height_counts.get(y, 0) + 1

print("Blocks by height level:")
for y in sorted(height_counts.keys()):
    print(f"  Y={y}: {height_counts[y]} blocks")
    """)
    
    print()
    print("Example 2: Search specific tile range")
    print("-" * 70)
    print("""
from search import search_blocks_in_area
from connector import BlueMapConnector

connector = BlueMapConnector("http://localhost:8100")

# Search tiles from (-5, -5) to (5, 5)
all_blocks = []

for x, y, z in search_blocks_in_area(
    connector,
    map_id="world",
    min_tile_x=-5,
    max_tile_x=5,
    min_tile_z=-5,
    max_tile_z=5,
    verbose=True
):
    all_blocks.append((x, y, z))

print(f"Total blocks found: {len(all_blocks)}")
    """)
    
    print()
    print("Example 3: Export to CSV with custom processing")
    print("-" * 70)
    print("""
from search import search_blocks_in_radius, export_to_csv
from connector import BlueMapConnector

connector = BlueMapConnector("http://localhost:8100")

# Collect surface blocks that might be trees
tree_height_blocks = []

for x, y, z in search_blocks_in_radius(
    connector,
    map_id="world",
    center_x=0,
    center_z=0,
    radius=10,
    min_y=60,
    max_y=100,
    verbose=True
):
    tree_height_blocks.append((x, y, z))

# Export to CSV
export_to_csv(tree_height_blocks, "potential_tree_blocks.csv")

print(f"Exported {len(tree_height_blocks)} block positions to CSV")
print("Note: These are all blocks at tree height, not specifically oak logs")
    """)
    
    print()
    print("Example 4: Find blocks near a specific coordinate")
    print("-" * 70)
    print("""
from search import search_blocks_in_radius
from connector import BlueMapConnector

connector = BlueMapConnector("http://localhost:8100")

# Convert world coordinates to tile coordinates
target_world_x, target_world_z = 100, 200
target_tile_x, target_tile_z = connector.world_to_tile_coordinates(
    target_world_x, target_world_z, grid_size=16
)

# Search 2 tiles around that location
nearby_blocks = []

for x, y, z in search_blocks_in_radius(
    connector,
    map_id="world",
    center_x=target_tile_x,
    center_z=target_tile_z,
    radius=2,
    verbose=True
):
    # Calculate distance from target
    distance = ((x - target_world_x)**2 + (z - target_world_z)**2)**0.5
    
    if distance <= 20:  # Within 20 blocks
        nearby_blocks.append((x, y, z, distance))

# Sort by distance
nearby_blocks.sort(key=lambda b: b[3])

print(f"Found {len(nearby_blocks)} blocks within 20 blocks of ({target_world_x}, {target_world_z})")
for x, y, z, dist in nearby_blocks[:10]:
    print(f"  ({x}, {y}, {z}) - {dist:.1f} blocks away")
    """)


def example_oak_log_search_capabilities():
    """Explain the capabilities for searching for specific block types."""
    
    print()
    print("=" * 70)
    print("Searching for Oak Logs - NOW FULLY SUPPORTED! ✨")
    print("=" * 70)
    print()
    
    print("THE SOLUTION:")
    print("-" * 70)
    print("The tool now uses textures.json to map PRBM material IDs to block types!")
    print("This allows identification of specific blocks like oak logs, diamond ore, etc.")
    print()
    
    print("WHAT YOU CAN DO:")
    print("-" * 70)
    print("1. Find specific block types (✓) - NEW!")
    print("2. Search for oak logs specifically (✓) - NEW!")
    print("3. Filter by height range (✓)")
    print("4. Get exact in-game coordinates (✓)")
    print("5. Export to CSV for further analysis (✓)")
    print()
    
    print("EXAMPLES:")
    print("-" * 70)
    print()
    print("1. Search for oak logs:")
    print("   $ python search.py http://localhost:8100 world --radius 10 \\")
    print("           --block-type minecraft:block/oak_log")
    print()
    print("2. Search for oak logs at surface level only:")
    print("   $ python search.py http://localhost:8100 world --radius 10 \\")
    print("           --block-type minecraft:block/oak_log --min-y 60 --max-y 100")
    print()
    print("3. Search for diamond ore at diamond level:")
    print("   $ python search.py http://localhost:8100 world --radius 20 \\")
    print("           --block-type minecraft:block/diamond_ore --min-y -64 --max-y 16")
    print()
    print("4. Search for any spruce wood blocks:")
    print("   $ python search.py http://localhost:8100 world --radius 5 \\")
    print("           --block-type minecraft:block/spruce_log")
    print()
    print("5. Export oak log coordinates to CSV:")
    print("   $ python search.py http://localhost:8100 world --radius 10 \\")
    print("           --block-type minecraft:block/oak_log --output oak_logs.csv")
    print()
    
    print("HOW IT WORKS:")
    print("-" * 70)
    print("1. The tool fetches textures.json from the BlueMap server")
    print("2. This file maps material IDs (indices) to block resource paths")
    print("3. When parsing PRBM, material IDs are matched against this mapping")
    print("4. Only vertices with matching material IDs are returned as results")
    print()
    print("This is a COMPLETE solution for finding specific block types!")
    print()
    print("This would give you block-type information that PRBM rendering data")
    print("simply doesn't contain.")
    print()


def main():
    """Run all example demonstrations."""
    
    example_command_line_usage()
    example_programmatic_usage()
    example_oak_log_search_capabilities()
    
    print("=" * 70)
    print()


if __name__ == "__main__":
    main()
