# PRBM Parser Implementation - Summary

## Overview

This implementation adds complete PRBM (Packed Region Binary Model) file parsing capabilities to the BlueMap connector, enabling extraction of block positions in Minecraft world coordinates.

## Problem Solved

The original problem statement requested:
1. **Implement handling for PRBM files** - ✅ Complete
2. **Figure out how they work** - ✅ Analyzed PRBMWriter.java and documented format
3. **Implement a parser in Python** - ✅ Full parser with all 7 attributes
4. **Find block function to give in-game coordinates** - ✅ `find_blocks()` returns world coordinates

## Implementation Details

### Core Components

1. **PRBM Parser** (`parse_prbm_tile`)
   - Parses binary PRBM format
   - Extracts all 7 standard attributes:
     - position (3D float, 32-bit)
     - normal (3D normalized, 8-bit signed)
     - color (3D normalized, 8-bit unsigned)
     - uv (2D float, 32-bit)
     - ao (scalar normalized, 8-bit unsigned)
     - blocklight (scalar, 8-bit signed)
     - sunlight (scalar, 8-bit signed)
   - Parses material groups
   - Robust bounds checking
   - Clear error messages

2. **find_blocks() Function**
   - Downloads and parses PRBM tiles
   - Extracts vertex positions
   - Converts to unique block positions
   - Returns in-game world coordinates
   - Includes metadata (bounds, triangles, colors, materials)

3. **Coordinate Conversion**
   - `tile_to_world_coordinates()`: Tile coords → World bounds
   - `world_to_tile_coordinates()`: World coords → Tile coords
   - Configurable grid size and offsets

### PRBM Format Details

```
Header (8 bytes):
  - Version (1 byte): Currently 1
  - Format bits (1 byte): indexed | endianness | attribute count
  - Num values (3 bytes, little-endian)
  - Num indices (3 bytes, little-endian)

Attributes (7 standard):
  Each attribute has:
  - Name (null-terminated ASCII string)
  - Type byte (float/int, normalized, cardinality, encoding)
  - Padding to 4-byte alignment
  - Data array

Material Groups:
  - Padding to 4-byte alignment
  - Material ID (4 bytes)
  - Start index (4 bytes)
  - Count (4 bytes)
  - Terminated with -1
```

### Coordinate System

BlueMap uses a grid-based system:
- Default tile size: 16 blocks
- Tile (x, z) covers world blocks:
  - Min: `(x * 16, z * 16)`
  - Max: `((x+1) * 16 - 1, (z+1) * 16 - 1)`

Examples:
- Tile (0, 0) → World blocks (0, 0) to (15, 15)
- Tile (1, 1) → World blocks (16, 16) to (31, 31)
- Tile (-1, -1) → World blocks (-16, -16) to (-1, -1)

## Testing

Three comprehensive test suites:

1. **PRBM Parser Test**
   - Creates synthetic PRBM file
   - Validates parsing of all attributes
   - Verifies position and color extraction

2. **Coordinate Conversion Test**
   - Tests tile-to-world conversion
   - Tests world-to-tile conversion
   - Validates negative coordinates
   - Tests different grid sizes and offsets

3. **Malformed Data Test**
   - Tests truncated files
   - Tests invalid versions
   - Validates error messages
   - Ensures no crashes

**All tests pass: 100% success rate**

## Usage Examples

### Basic Usage

```python
from connector import BlueMapConnector

connector = BlueMapConnector("http://localhost:8100")

# Find blocks in a tile
result = connector.find_blocks("world", tile_x=0, tile_z=0)

print(f"Found {len(result['block_positions'])} blocks")
for x, y, z in result['block_positions'][:10]:
    print(f"  Block at ({x}, {y}, {z})")
```

### Scanning an Area

```python
# Scan 5x5 tiles around spawn
all_blocks = set()

for tile_x in range(-2, 3):
    for tile_z in range(-2, 3):
        try:
            result = connector.find_blocks('world', tile_x, tile_z)
            all_blocks.update(result['block_positions'])
        except:
            pass

print(f"Found {len(all_blocks)} unique blocks")
```

### Filtering by Height

```python
result = connector.find_blocks('world', 0, 0)

surface = [pos for pos in result['block_positions'] if pos[1] >= 64]
underground = [pos for pos in result['block_positions'] if pos[1] < 64]

print(f"Surface: {len(surface)}, Underground: {len(underground)}")
```

## Documentation

Comprehensive documentation provided in:

1. **CONNECTOR_README.md**: Complete API reference with examples
2. **prbm_examples.py**: Basic usage examples
3. **demo_prbm.py**: Full workflow demonstration
4. **practical_example.py**: Real-world scenarios
5. **This file**: Implementation summary

## Security & Robustness

- ✅ Bounds checking on all buffer reads
- ✅ Proper error handling for malformed files
- ✅ Clear, actionable error messages
- ✅ Uses parsed attribute count from header
- ✅ Handles edge cases (negative coordinates, etc.)

## Limitations

1. **Block Type Identification**: Cannot identify specific block types (e.g., "diamond_ore" vs "stone") because PRBM contains rendered geometry, not block metadata. Material IDs correspond to textures, not block types.

2. **Read-Only**: Parser is read-only; cannot modify or create PRBM files.

## Files Modified/Created

### Modified
- `connector.py`: Added parser, find_blocks, coordinate conversion
- `CONNECTOR_README.md`: Updated documentation
- `.gitignore`: Added CSV exclusion

### Created
- `test_prbm_parser.py`: Comprehensive test suite (398 lines)
- `prbm_examples.py`: Basic usage examples (162 lines)
- `demo_prbm.py`: Workflow demonstration (130 lines)
- `practical_example.py`: Real-world scenarios (277 lines)

## Performance Considerations

- Parser reads files sequentially, avoiding unnecessary memory copies
- Block positions stored in set for O(1) duplicate detection
- Coordinate conversion uses simple arithmetic (O(1))
- No external dependencies beyond `requests` and stdlib

## Future Enhancements

Potential areas for improvement:
1. Block type identification from material IDs (requires mapping)
2. Caching mechanisms for repeated queries
3. Async/parallel tile fetching for large areas
4. Compression support if PRBM adds it
5. Export to other formats (JSON, binary, database)

## Conclusion

This implementation provides a complete, production-ready PRBM parser that:
- ✅ Fully parses PRBM format
- ✅ Returns block positions in in-game coordinates
- ✅ Provides coordinate conversion utilities
- ✅ Includes robust error handling
- ✅ Has comprehensive tests
- ✅ Is well-documented with examples

The parser successfully addresses all requirements from the problem statement.
