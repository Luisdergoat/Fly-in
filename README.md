*This project has been created as part of the 42 curriculum by lunsold, Luisdergoat.*

# Fly-in

## Description

Fly-in is a drone routing simulation built as part of the 42 curriculum. Given a map that defines a directed graph of zones — a start hub, an end hub, and any number of waypoints — the program moves a fleet of drones from the start hub to the end hub in as few turns as possible while respecting zone capacity limits, link capacities, restricted zones, and impassable areas.

The simulation runs with a real-time pygame visualisation: zones and connections are rendered in a pixel-art style, drones are animated as they glide between zones each turn, and a heads-up display shows the current turn count and phase. When all drones reach the goal, a splash screen reports the total rounds and weighted move units.

Key features:
- **Custom map format** parsed at start-up (zones with coordinates, colors, and metadata)
- **Zone types**: `normal`, `priority`, `restricted`, `blocked`, `no_fly`
- **Capacity constraints**: per-zone maximum drones, per-link maximum throughput per turn
- **Restricted-zone transit**: moving into a restricted zone costs 2 move units and takes an extra turn to complete
- **Output file**: every turn's movements are written to `fly_in.txt`
- **Fullscreen / windowed mode** switchable via environment variable

## Instructions

### Requirements

- Python 3.9+
- pygame 2.x (installed automatically by `make install`)

### Installation

```bash
make install
```

This creates a Python virtual environment under `venv/` and installs all dependencies listed in `requirements.txt`.

### Running the simulation

```bash
make run maps/easy/01_linear_path.txt
```

Replace the map path with any `.txt` file from the `maps/` directory or your own map. The first positional argument after `run` is passed as the map file path.

**Environment variables**

| Variable | Default | Effect |
|---|---|---|
| `FLYIN_MAP` | *(CLI arg)* | Override the map path |
| `FLYIN_WINDOWED` | `0` | Set to `1` to run in a window instead of fullscreen |
| `FLYIN_VERBOSE` | `0` | Set to `1` to print zone state after each turn |
| `FLYIN_MAX_TURNS` | `10000` | Stop the simulation after this many turns |

### Controls

| Key | Action |
|---|---|
| `Space` | Start the simulation from the map preview screen |
| `Esc` / `Q` | Quit at any time |

### Makefile targets

| Target | Description |
|---|---|
| `make install` | Create venv and install dependencies |
| `make run <map>` | Run the simulation with the given map |
| `make debug <map>` | Run under Python's `pdb` debugger |
| `make lint` | Run `flake8` + `mypy` |
| `make clean` | Remove generated files and `__pycache__` |
| `make fclean` | Also remove the virtual environment |
| `make re` | Full clean and reinstall |

### Map file format

```
nb_drones: <count>

start_hub: <name> <x> <y> [color=<value> max_drones=<n>]
hub:       <name> <x> <y> [zone=<type> color=<value> max_drones=<n>]
end_hub:   <name> <x> <y> [color=<value> max_drones=<n>]

connection: <name_a>-<name_b> [max_link_capacity=<n>]
```

Zone types: `normal` (default), `priority`, `restricted`, `blocked`, `no_fly`.
Lines starting with `#` or `//` are comments.

## Algorithm

### Routing table — backwards Dijkstra from the goal

At startup the algorithm builds a distance table `dist_to_goal[zone]` using Dijkstra run **backwards** from every end-hub zone. For each zone the edge weight entering it is determined by its type:

- `normal` / `priority` → weight 1
- `restricted` → weight 2 (drones spend an extra turn in transit)
- `blocked` / `no_fly` → infinite (unreachable)

Running Dijkstra backwards on the reversed graph gives the optimal cost-to-goal for every reachable zone in one pass, without re-running search per drone.

### Per-turn decision: greedy best-first

Each turn, for every drone that is not yet in transit or at the goal:

1. Collect all zones reachable in one hop via the current zone's `connections` list.
2. Filter out zones with infinite `dist_to_goal` (dead ends or blocked).
3. Among feasible moves, pick the best by the tuple key `(dist_to_goal, -preference_rank, occupancy_pressure, zone_name)` — minimised lexicographically:
   - **distance to goal** first (closest wins)
   - **preference rank** as tiebreaker: end hub > priority > normal > restricted
   - **occupancy pressure** (`current_drones + pending_incoming`) to avoid overcrowded zones
   - **zone name** for deterministic tiebreaking

### Capacity-safe move application

All drone decisions for a turn are collected as *proposals* and then applied in a single pass ordered by distance-to-goal (drones closest to the goal move first). Before committing each move, a tentative state is checked against every zone's `max_drones` limit and, if configured, the link's `max_link_capacity`. Moves that would violate a constraint are silently skipped; the drone stays in place for that turn.

### Restricted-zone transit

Moving into a restricted zone does not place the drone immediately. Instead it is placed in an `_in_transit` dict with `(src, dst)`. On the *next* call to `begin_turn()` the drone is delivered into the destination zone. This two-turn transit models the higher cost of restricted airspace and is reflected visually by drawing the drone at the midpoint of the edge until delivery.

## Visual Representation

### Pixel-art map buffer

The map is rendered into a small off-screen surface (the *buffer*) at a resolution determined by the number and spread of zones, then scaled up with nearest-neighbour interpolation to fill the map panel. This produces a clean pixel-art look regardless of window size.

Zone positions in the buffer are computed from their `(x, y)` map coordinates, normalised into the available buffer area, with a configurable margin. A minimum neighbour distance is enforced: if zones would overlap, the cell size shrinks iteratively until separation is adequate.

### Zone nodes

Each zone is drawn as a coloured rectangle with rounded-corner shading. The accent colour comes from the zone's `color` metadata — including a dynamic **rainbow** mode that rotates hue over time. Hub types are distinguished by brightness and border style. A small tag letter (`S`, `Z`, `W`) is overlaid for start, end, and waypoint hubs, and the zone name is rendered below each node with a dark outline for legibility against any background.

### Connection lines

Directed connections between zones are drawn as anti-aliased lines in the buffer, coloured from a fixed palette that cycles per edge index. This allows the viewer to distinguish multiple outgoing connections from the same zone at a glance.

### Drone animation

Each drone is rendered twice — once in the buffer as a small circle (scaled with the cell size) and once as a larger screen-space overlay so individual drones remain visible even in dense maps. During a turn's animation phase, each drone glides smoothly from its source position to its destination along a sinusoidal path (unique amplitude, frequency, phase, and zigzag direction per drone) using a smootherstep easing curve. Drones in restricted transit are drawn at the midpoint of their edge.

### HUD and legend

A compact turn counter and phase label are drawn in the top-left corner with outlined text for contrast. A legend panel in the bottom-right corner lists every zone type and connection palette colour with a colour swatch. The start screen overlays a pulsing veil on the map with title and prompt text; the completion screen shows total rounds and weighted move units.

## Resources

- [Pygame documentation](https://www.pygame.org/docs/)
- [Python `heapq` module](https://docs.python.org/3/library/heapq.html)
- [Dijkstra's algorithm — Wikipedia](https://en.wikipedia.org/wiki/Dijkstra%27s_algorithm)
- [PEP 604 — Union type syntax](https://peps.python.org/pep-0604/)
- [mypy documentation](https://mypy.readthedocs.io/en/stable/)
- [flake8 documentation](https://flake8.pycqa.org/en/latest/)

### AI usage

Claude (Anthropic) was used during this project for the following tasks:
- Designing the pygame rendering pipeline (pixel-art, scaling, smootherstep curve)
- Resolving mypy type errors across the codebase (union syntax, variable type conflicts, untyped function bodies)
- Writing this README
