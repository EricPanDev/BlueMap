#!/usr/bin/env python3
"""
Practical example: Finding blocks in a specific area

This example demonstrates how to use the PRBM parser to:
1. Find all blocks in a rectangular area
2. Filter blocks by height (e.g., surface vs underground)
3. Count unique block positions
4. Export results
"""

from connector import BlueMapConnector
from typing import List, Tuple, Set


def find_blocks_in_area(
    connector: BlueMapConnector,
    map_id: str,
    min_tile_x: int,
    max_tile_x: int,
    min_tile_z: int,
    max_tile_z: int,
    verbose: bool = True
) -> Set[Tuple[int, int, int]]:
    """
    Find all blocks in a rectangular tile area.
    
    Args:
        connector: BlueMapConnector instance
        map_id: Map ID to search
        min_tile_x, max_tile_x: X tile coordinate range
        min_tile_z, max_tile_z: Z tile coordinate range
        verbose: Whether to print progress
        
    Returns:
        Set of unique (x, y, z) block positions
    """
    all_blocks = set()
    tiles_processed = 0
    tiles_skipped = 0
    
    for tile_x in range(min_tile_x, max_tile_x + 1):
        for tile_z in range(min_tile_z, max_tile_z + 1):
            try:
                result = connector.find_blocks(map_id, tile_x, tile_z)
                blocks = result['block_positions']
                all_blocks.update(blocks)
                tiles_processed += 1
                
                if verbose:
                    print(f"  Tile ({tile_x:3d}, {tile_z:3d}): "
                          f"{len(blocks):5d} blocks, "
                          f"{result['num_triangles']:5d} triangles")
                    
            except Exception as e:
                tiles_skipped += 1
                if verbose:
                    print(f"  Tile ({tile_x:3d}, {tile_z:3d}): Skipped ({e})")
    
    if verbose:
        print(f"\nProcessed {tiles_processed} tiles, skipped {tiles_skipped}")
        print(f"Found {len(all_blocks)} unique block positions")
    
    return all_blocks


def filter_blocks_by_height(
    blocks: Set[Tuple[int, int, int]],
    min_y: int = None,
    max_y: int = None
) -> List[Tuple[int, int, int]]:
    """
    Filter blocks by Y coordinate (height).
    
    Args:
        blocks: Set of block positions
        min_y: Minimum Y coordinate (inclusive), None for no limit
        max_y: Maximum Y coordinate (inclusive), None for no limit
        
    Returns:
        Filtered list of block positions
    """
    filtered = []
    for x, y, z in blocks:
        if min_y is not None and y < min_y:
            continue
        if max_y is not None and y > max_y:
            continue
        filtered.append((x, y, z))
    
    return filtered


def analyze_height_distribution(blocks: Set[Tuple[int, int, int]]) -> dict:
    """
    Analyze the vertical distribution of blocks.
    
    Args:
        blocks: Set of block positions
        
    Returns:
        Dictionary with height statistics
    """
    if not blocks:
        return {
            'min_y': None,
            'max_y': None,
            'range': 0,
            'counts_by_y': {}
        }
    
    y_values = [y for x, y, z in blocks]
    min_y = min(y_values)
    max_y = max(y_values)
    
    # Count blocks at each Y level
    counts_by_y = {}
    for x, y, z in blocks:
        counts_by_y[y] = counts_by_y.get(y, 0) + 1
    
    return {
        'min_y': min_y,
        'max_y': max_y,
        'range': max_y - min_y,
        'counts_by_y': counts_by_y
    }


def export_blocks_to_csv(
    blocks: List[Tuple[int, int, int]],
    filename: str
):
    """
    Export block positions to CSV file.
    
    Args:
        blocks: List of block positions
        filename: Output CSV filename
    """
    with open(filename, 'w') as f:
        f.write("x,y,z\n")
        for x, y, z in sorted(blocks):
            f.write(f"{x},{y},{z}\n")
    
    print(f"Exported {len(blocks)} blocks to {filename}")


def main_example():
    """
    Main example demonstrating practical usage.
    
    Note: This requires a running BlueMap server.
    Modify the URL and coordinates for your setup.
    """
    
    print("=" * 70)
    print("Practical Example: Finding Blocks in an Area")
    print("=" * 70)
    
    # This would connect to a real server
    # For demonstration, we'll show what the code would do
    
    print("\n1. Connecting to BlueMap server...")
    print("   connector = BlueMapConnector('http://localhost:8100')")
    
    print("\n2. Finding blocks in a 5x5 tile area around spawn...")
    print("   blocks = find_blocks_in_area(")
    print("       connector, 'world',")
    print("       min_tile_x=-2, max_tile_x=2,")
    print("       min_tile_z=-2, max_tile_z=2")
    print("   )")
    
    print("\n   Example output:")
    print("     Tile ( -2,  -2):   450 blocks,  1240 triangles")
    print("     Tile ( -2,  -1):   523 blocks,  1356 triangles")
    print("     Tile ( -2,   0):   489 blocks,  1298 triangles")
    print("     ...")
    print("     Processed 25 tiles, skipped 0")
    print("     Found 11250 unique block positions")
    
    print("\n3. Analyzing height distribution...")
    print("   stats = analyze_height_distribution(blocks)")
    print("   print(f'Height range: {stats['min_y']} to {stats['max_y']}')")
    
    print("\n   Example output:")
    print("     Height range: -64 to 256")
    print("     Range: 320 blocks")
    
    print("\n4. Filtering blocks by height...")
    print("   surface_blocks = filter_blocks_by_height(blocks, min_y=64)")
    print("   underground_blocks = filter_blocks_by_height(blocks, max_y=63)")
    print("   bedrock_level = filter_blocks_by_height(blocks, min_y=-64, max_y=-60)")
    
    print("\n   Example output:")
    print("     Surface blocks (y >= 64): 6543")
    print("     Underground blocks (y <= 63): 4707")
    print("     Bedrock level (-64 to -60): 234")
    
    print("\n5. Finding blocks in a specific height range...")
    print("   diamond_level = filter_blocks_by_height(blocks, min_y=-64, max_y=16)")
    print("   print(f'Blocks at diamond level: {len(diamond_level)}')")
    
    print("\n   Example output:")
    print("     Blocks at diamond level: 3421")
    
    print("\n6. Exporting results...")
    print("   export_blocks_to_csv(surface_blocks, 'surface_blocks.csv')")
    print("   export_blocks_to_csv(diamond_level, 'diamond_level.csv')")
    
    print("\n   Example output:")
    print("     Exported 6543 blocks to surface_blocks.csv")
    print("     Exported 3421 blocks to diamond_level.csv")
    
    print("\n" + "=" * 70)
    print("Complete Usage Example")
    print("=" * 70)
    print("""
# Full working code (requires running BlueMap server):

from connector import BlueMapConnector

# Connect
connector = BlueMapConnector("http://localhost:8100")

# Find all blocks in a 5x5 tile area
blocks = find_blocks_in_area(
    connector, 'world',
    min_tile_x=-2, max_tile_x=2,
    min_tile_z=-2, max_tile_z=2
)

# Analyze height distribution
stats = analyze_height_distribution(blocks)
print(f"Height range: {stats['min_y']} to {stats['max_y']}")
print(f"Total blocks: {len(blocks)}")

# Filter by height
surface_blocks = filter_blocks_by_height(blocks, min_y=64)
underground_blocks = filter_blocks_by_height(blocks, max_y=63)
diamond_level = filter_blocks_by_height(blocks, min_y=-64, max_y=16)

print(f"Surface blocks: {len(surface_blocks)}")
print(f"Underground blocks: {len(underground_blocks)}")
print(f"Diamond level blocks: {len(diamond_level)}")

# Export to CSV
export_blocks_to_csv(surface_blocks, 'surface_blocks.csv')
export_blocks_to_csv(diamond_level, 'diamond_level.csv')

# Find specific coordinates
target_block = (100, 64, 200)
if target_block in blocks:
    print(f"Block {target_block} exists in the scanned area")
    tile = connector.world_to_tile_coordinates(100, 200)
    print(f"It's in tile {tile}")
    """)
    
    print("=" * 70)


if __name__ == "__main__":
    main_example()
