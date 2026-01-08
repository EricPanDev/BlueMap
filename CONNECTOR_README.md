# BlueMap Web API Connector

A Python API connector for interacting with hosted BlueMap instances. This tool allows you to programmatically access BlueMap data through the web API.

## Features

- Connect to any hosted BlueMap instance via URL
- Fetch map settings and metadata
- Request map tiles (both high-res and low-res)
- **Parse PRBM (high-resolution tile) files**
- **Extract block positions in in-game world coordinates**
- **Convert between tile and world coordinates**
- Search for blocks within chunks/tiles
- Check tile existence without full download
- Fetch multiple tiles in an area

## Installation

No additional dependencies are required beyond Python's standard library and `requests`:

```bash
pip install requests
```

## Quick Start

### Basic Usage

```python
from connector import BlueMapConnector

# Connect to your BlueMap instance
connector = BlueMapConnector("http://localhost:8100")

# Get available maps
maps = connector.get_maps()
print(f"Available maps: {list(maps.keys())}")

# Get map settings
map_settings = connector.get_map_settings("world")
print(f"Map name: {map_settings['name']}")
```

### Finding Blocks with In-Game Coordinates

```python
# Find all blocks in a tile and get their in-game coordinates
result = connector.find_blocks(
    map_id="world",
    tile_x=0,
    tile_z=0
)

print(f"Tile covers world coordinates: {result['world_bounds']}")
print(f"Found {len(result['block_positions'])} unique blocks")
print(f"Number of triangles: {result['num_triangles']}")

# Print first 10 block positions
for x, y, z in result['block_positions'][:10]:
    print(f"  Block at world coordinates ({x}, {y}, {z})")
```

### Parsing PRBM Tiles

```python
# Download and parse a PRBM tile
tile_data = connector.get_tile(map_id="world", x=0, z=0, lod=0)
parsed = connector.parse_prbm_tile(tile_data)

print(f"Version: {parsed['version']}")
print(f"Triangles: {parsed['num_triangles']}")
print(f"Vertices: {parsed['num_values']}")

# Access vertex positions
for i, (x, y, z) in enumerate(parsed['positions'][:5]):
    print(f"  Vertex {i}: ({x:.2f}, {y:.2f}, {z:.2f})")

# Access vertex colors
for i, (r, g, b) in enumerate(parsed['colors'][:5]):
    print(f"  Color {i}: RGB({r:.2f}, {g:.2f}, {b:.2f})")
```

### Coordinate Conversion

```python
# Convert tile coordinates to world coordinates
tile_x, tile_z = 0, 0
bounds = connector.tile_to_world_coordinates(tile_x, tile_z)
print(f"Tile ({tile_x}, {tile_z}) covers world coords {bounds[0]} to {bounds[1]}")

# Convert world coordinates to tile coordinates
world_x, world_z = 100, 200
tile = connector.world_to_tile_coordinates(world_x, world_z)
print(f"World position ({world_x}, {world_z}) is in tile {tile}")
```

### Searching for Blocks

```python
# Search for tiles in an area (to find where blocks might be)
results = connector.search_block(
    "diamond_ore",
    map_id="world",
    center_x=0,
    center_z=0,
    radius=5
)

print(f"Found {len(results)} tiles in search area")
for x, z in results:
    print(f"  Tile at ({x}, {z})")
```

### Fetching Tiles

```python
# Get a specific tile
tile_data = connector.get_tile(map_id="world", x=0, z=0, lod=0)
print(f"Downloaded tile data: {len(tile_data)} bytes")

# Check if a tile exists
exists = connector.check_tile_exists(map_id="world", x=5, z=10)
print(f"Tile exists: {exists}")

# Get all tiles in an area
tiles = connector.get_tiles_in_area(
    map_id="world",
    min_x=-2, max_x=2,
    min_z=-2, max_z=2,
    lod=0
)
print(f"Downloaded {len(tiles)} tiles")
```

## Command-Line Usage

### connector.py

You can run the connector directly from the command line:

```bash
python connector.py http://localhost:8100
```

This will:
1. Connect to the specified BlueMap instance
2. Display available maps and their settings
3. Perform an example tile search

### search.py - Block Position Search Tool

The `search.py` script provides a command-line interface for searching and extracting block positions from BlueMap servers:

```bash
# Search for blocks in a 5-tile radius around spawn
python search.py http://localhost:8100 world --radius 5

# Search with height filter (surface level where trees grow)
python search.py http://localhost:8100 world --radius 3 --min-y 60 --max-y 100

# Export results to CSV
python search.py http://localhost:8100 world --radius 2 --output blocks.csv
```

**Key Features:**
- Search blocks in a radius or specific tile range
- Filter by height (Y coordinate)
- Export coordinates to CSV
- Yields in-game world coordinates
- Progress reporting

**Important Limitation:**
The search tool can find block *positions* but cannot identify block *types* (e.g., cannot distinguish oak logs from stone) because PRBM files only contain rendering geometry, not block metadata. Material IDs correspond to textures, not block types.

For detailed usage examples and limitations, see `search_examples.py`:

```bash
python search_examples.py
```

#### search.py Usage

```
python search.py [-h] (--radius N | --tile-range MIN MAX) 
                 [--center X,Z] [--min-y Y] [--max-y Y] 
                 [--output FILE] [--limit N] [--quiet] [--timeout SECONDS]
                 url map_id
```

**Positional arguments:**
- `url` - BlueMap server URL (e.g., http://localhost:8100)
- `map_id` - Map ID to search (e.g., world, world_nether)

**Search area options:**
- `--radius N` - Search radius in tiles around center
- `--tile-range MIN MAX` - Tile range as "x1,z1" "x2,z2"
- `--center X,Z` - Center tile coordinates for radius search (default: 0,0)

**Filters:**
- `--min-y Y` - Minimum Y coordinate (height) filter
- `--max-y Y` - Maximum Y coordinate (height) filter

**Output options:**
- `--output FILE, -o FILE` - Export coordinates to CSV file
- `--limit N` - Maximum number of coordinates to return
- `--quiet, -q` - Suppress progress messages
- `--timeout SECONDS` - Request timeout in seconds (default: 30)

#### Programmatic Usage of search.py

The search functions can also be imported and used programmatically:

```python
from search import search_blocks_in_radius, export_to_csv
from connector import BlueMapConnector

connector = BlueMapConnector("http://localhost:8100")

# Search for surface blocks
surface_blocks = []
for x, y, z in search_blocks_in_radius(
    connector,
    map_id="world",
    center_x=0,
    center_z=0,
    radius=5,
    min_y=60,  # Surface level
    max_y=100,
    verbose=True
):
    surface_blocks.append((x, y, z))

# Export to CSV
export_to_csv(surface_blocks, "surface_blocks.csv")
```

## API Reference

### BlueMapConnector

#### `__init__(base_url, timeout=10)`

Initialize the connector.

- `base_url`: The base URL of the BlueMap web interface (e.g., "http://x.x.x.x:8100")
- `timeout`: Request timeout in seconds (default: 10)

#### `get_settings(force_refresh=False)`

Fetch the main settings.json from the BlueMap instance.

Returns: Dictionary containing BlueMap settings

#### `get_maps(force_refresh=False)`

Get information about all available maps.

Returns: Dictionary mapping map IDs to their metadata

#### `get_map_settings(map_id)`

Fetch the settings.json for a specific map.

- `map_id`: The ID of the map

Returns: Dictionary containing map-specific settings

#### `get_tile(map_id, x, z, lod=0)`

Fetch the raw data for a specific tile.

- `map_id`: The ID of the map
- `x`: Tile X coordinate
- `z`: Tile Z coordinate
- `lod`: Level of detail (0 for hires, 1+ for lowres)

Returns: Raw tile data as bytes

#### `check_tile_exists(map_id, x, z, lod=0)`

Check if a tile exists without downloading its full content.

Returns: True if the tile exists, False otherwise

#### `search_block(block_name, map_id, center_x=0, center_z=0, radius=10, lod=0, verbose=True)`

Search for chunks/tiles that may contain a specific block.

- `block_name`: The block name to search for (e.g., "diamond_ore")
- `map_id`: The ID of the map to search
- `center_x`: Center X tile coordinate
- `center_z`: Center Z tile coordinate
- `radius`: Search radius in tiles
- `lod`: Level of detail to use (0 for hires)
- `verbose`: If True, print progress messages (default: True)

Returns: List of (x, z) tile coordinates where tiles exist

**Note**: Since PRBM files are binary geometry data, this method can only determine which chunks exist (have been generated/rendered), not the exact block contents. A complete implementation would need to fully parse the PRBM format to identify specific blocks.

#### `get_tiles_in_area(map_id, min_x, max_x, min_z, max_z, lod=0)`

Fetch all tiles in a rectangular area.

Returns: List of tuples (x, z, tile_data) for each existing tile

#### `parse_prbm_tile(data)`

Parse a PRBM (BlueMap high-resolution tile) file.

- `data`: Raw PRBM file data as bytes

Returns: Dictionary with parsed tile information including:
- `version`: Format version
- `num_triangles`: Number of triangles
- `num_values`: Number of vertices
- `positions`: List of (x, y, z) vertex positions
- `colors`: List of (r, g, b) vertex colors (normalized 0.0-1.0)
- `materials`: Material group information
- Other attributes (uvs, ao, lighting, normals)

#### `find_blocks(map_id, tile_x, tile_z, grid_size=16, offset_x=0, offset_z=0, lod=0)`

Find and return block positions from a PRBM tile in in-game coordinates.

- `map_id`: The ID of the map
- `tile_x`: Tile X coordinate
- `tile_z`: Tile Z coordinate
- `grid_size`: Size of each tile in blocks (default: 16)
- `offset_x`: Grid offset in X direction (default: 0)
- `offset_z`: Grid offset in Z direction (default: 0)
- `lod`: Level of detail (must be 0 for PRBM tiles)

Returns: Dictionary containing:
- `tile_coords`: (tile_x, tile_z) coordinates
- `world_bounds`: ((min_x, min_z), (max_x, max_z)) world coordinate bounds
- `num_triangles`: Number of triangles in the tile
- `num_vertices`: Number of vertices
- `block_positions`: List of unique (x, y, z) block positions in world coordinates
- `vertex_positions`: List of all (x, y, z) vertex positions
- `materials`: Material group information
- `colors`: Vertex color information

**This is the recommended method to get block positions in in-game coordinates.**

#### `tile_to_world_coordinates(tile_x, tile_z, grid_size=16, offset_x=0, offset_z=0)`

Convert tile coordinates to world coordinate ranges.

- `tile_x`: Tile X coordinate
- `tile_z`: Tile Z coordinate
- `grid_size`: Size of each tile in blocks (default: 16)
- `offset_x`: Grid offset in X direction (default: 0)
- `offset_z`: Grid offset in Z direction (default: 0)

Returns: Tuple of ((min_x, min_z), (max_x, max_z)) world coordinates

#### `world_to_tile_coordinates(world_x, world_z, grid_size=16, offset_x=0, offset_z=0)`

Convert world coordinates to tile coordinates.

- `world_x`: World X coordinate
- `world_z`: World Z coordinate
- `grid_size`: Size of each tile in blocks (default: 16)
- `offset_x`: Grid offset in X direction (default: 0)
- `offset_z`: Grid offset in Z direction (default: 0)

Returns: Tuple of (tile_x, tile_z) coordinates

## PRBM Format

PRBM (Packed Region Binary Model) is BlueMap's custom binary format for high-resolution tiles. Each PRBM file contains:

### File Structure

1. **Header** (2 bytes):
   - Version byte (currently 1)
   - Format bits (indexed flag, endianness, attribute count)

2. **Counts** (6 bytes):
   - Number of values (3 bytes, little-endian)
   - Number of indices (3 bytes, little-endian, 0 for non-indexed)

3. **Attributes** (7 standard attributes):
   - **position**: 3D vertex positions (float, 32-bit)
   - **normal**: Surface normals (normalized, 8-bit signed)
   - **color**: RGB colors (normalized, 8-bit unsigned)
   - **uv**: Texture coordinates (float, 32-bit)
   - **ao**: Ambient occlusion (normalized, 8-bit unsigned)
   - **blocklight**: Block light levels (8-bit signed)
   - **sunlight**: Sunlight levels (8-bit signed)

4. **Material Groups**:
   - Groups of triangles by material ID
   - Terminated with -1

### Coordinate System

BlueMap uses a grid-based coordinate system:

- Each tile covers a rectangular area in the world
- Default grid size is 16 blocks per tile
- Tile (x, z) covers world coordinates:
  - Min: `(x * grid_size + offset, z * grid_size + offset)`
  - Max: `((x+1) * grid_size + offset - 1, (z+1) * grid_size + offset - 1)`

Example with default settings (grid_size=16, offset=0):
- Tile (0, 0) covers world blocks (0, 0) to (15, 15)
- Tile (1, 1) covers world blocks (16, 16) to (31, 31)
- Tile (-1, -1) covers world blocks (-16, -16) to (-1, -1)

## BlueMap Tile Structure

BlueMap organizes tiles using a hierarchical directory structure:

- High-resolution tiles: `maps/{map_id}/tiles/0/x{x_path}z{z_path}.prbm`
- Low-resolution tiles: `maps/{map_id}/tiles/{lod}/x{x_path}z{z_path}.png`

Where coordinates are split per digit:
- `x=123` becomes `x1/2/3/`
- `z=-45` becomes `z-4/5/`

Example: Tile at (123, -45) with LOD 0:
```
maps/world/tiles/0/x1/2/3/z-4/5.prbm
```

## Limitations

- **Block type identification**: While the parser extracts block positions from PRBM geometry, it cannot identify the specific block type (e.g., "oak_log" vs "stone") because PRBM files only contain rendered geometry, not block metadata. Material IDs in the PRBM correspond to textures, not block types.
  
  **Workaround**: The `search.py` tool can find block positions and filter by height (Y coordinate), which can help narrow down blocks to surface level (where trees grow) or specific underground levels. However, you still cannot distinguish between different block types at those positions using only PRBM data.
  
- **Read-only**: This connector only supports reading data from BlueMap. It cannot modify or upload data.

## Advanced Examples

### Example 1: Scan Area for All Blocks

```python
from connector import BlueMapConnector

# Connect
connector = BlueMapConnector("http://example.com:8100", timeout=30)

# Get all maps
maps = connector.get_maps()

# Scan a 5x5 tile area around spawn
all_blocks = set()

for tile_x in range(-2, 3):
    for tile_z in range(-2, 3):
        try:
            result = connector.find_blocks('world', tile_x, tile_z)
            blocks = result['block_positions']
            all_blocks.update(blocks)
            print(f"Tile ({tile_x}, {tile_z}): {len(blocks)} blocks")
        except Exception as e:
            print(f"Tile ({tile_x}, {tile_z}): Not available")

print(f"\nTotal unique blocks: {len(all_blocks)}")
```

### Example 2: Filter Blocks by Height

```python
# Find all surface blocks (y >= 64)
result = connector.find_blocks('world', tile_x=0, tile_z=0)

surface_blocks = [
    (x, y, z) for x, y, z in result['block_positions']
    if y >= 64
]

underground_blocks = [
    (x, y, z) for x, y, z in result['block_positions']
    if y < 64
]

print(f"Surface blocks: {len(surface_blocks)}")
print(f"Underground blocks: {len(underground_blocks)}")
```

### Example 3: Parse PRBM File Directly

```python
# If you have a PRBM file locally
with open('tile.prbm', 'rb') as f:
    prbm_data = f.read()

# Parse it
parsed = connector.parse_prbm_tile(prbm_data)

print(f"Version: {parsed['version']}")
print(f"Triangles: {parsed['num_triangles']}")
print(f"Vertices: {parsed['num_values']}")

# Access vertex data
for i, pos in enumerate(parsed['positions'][:5]):
    color = parsed['colors'][i]
    print(f"Vertex {i}: pos={pos}, color={color}")
```

## Contributing

Contributions are welcome! Areas for improvement:

1. ~~Complete PRBM parser implementation~~ ✓ Implemented!
2. Block type identification from material IDs
3. Caching mechanisms for better performance
4. Async/parallel tile fetching
5. Additional utility functions for common operations
6. Better error handling and retry logic

## License

This connector is provided as part of the BlueMap project and follows the same MIT License.
