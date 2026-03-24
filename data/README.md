# Data Guide

This folder contains all graph data for the Optimal Dog Walking Route project.

## Folder Structure

```
data/
├── sample_data.json          ← original 5-node example (used by app.py default)
├── sample_data/              ← richer hand-crafted scenarios
│   ├── urban_downtown.json        20 nodes, 32 edges — dense city block
│   ├── suburban_park_district.json 20 nodes, 30 edges — quiet suburb with parks/trails
│   └── large_city_loop.json       30 nodes, 55 edges — mixed urban + suburban
└── real_locations/           ← placeholder for future real-world OSM data
```

---

## JSON Schema

Every JSON file must have two top-level arrays: `nodes` and `edges`.

### Node fields

| Field       | Type   | Required | Description                                                  |
|-------------|--------|----------|--------------------------------------------------------------|
| `node_id`   | int    | yes      | Unique identifier, sequential from 0                        |
| `name`      | string | yes      | Human-readable place name                                    |
| `node_type` | string | yes      | See node types table below                                   |
| `reward`    | float  | yes      | −10 (worst) to 10 (best). See reward scale below            |
| `x`         | float  | yes      | Spatial x-coordinate for map visualisation                  |
| `y`         | float  | yes      | Spatial y-coordinate for map visualisation                  |

### Edge fields

| Field         | Type  | Required | Description                                          |
|---------------|-------|----------|------------------------------------------------------|
| `from_id`     | int   | yes      | Source node_id                                       |
| `to_id`       | int   | yes      | Destination node_id                                  |
| `time_cost`   | float | yes      | Walking time in minutes (>= 0)                       |
| `edge_reward` | float | yes      | Path-level reward (−10 to 10)                        |

> **Do NOT include `final_weight` in JSON files.** It is computed automatically
> by `Graph.add_edge` using: `final_weight = time_cost - edge_reward - dest_node.reward`

---

## Node Types

| node_type      | Description                        | Typical reward |
|----------------|------------------------------------|----------------|
| `home`         | Starting/ending point              | 0              |
| `park`         | Green space, dog-friendly area     | 5–10           |
| `trail`        | Walking path, scenic route         | 3–8            |
| `rest_stop`    | Bench, café, water fountain        | 2–5            |
| `intersection` | Street crossing, neutral location  | 0              |
| `trigger_zone` | Construction, heavy traffic        | −10            |

## Reward Scale

| Score   | Meaning         | Examples                           |
|---------|-----------------|------------------------------------|
| −10     | Trigger zone    | Construction site, heavy traffic   |
| 0       | Neutral         | Ordinary sidewalk, intersection    |
| 1–4     | Mildly pleasant | Quiet street, shaded path, café    |
| 5–7     | Good            | Grass area, gentle trail           |
| 8–10    | Excellent       | Off-leash park, dog water fountain |

---

## How to Load a Dataset

### In the Streamlit app
1. Run `streamlit run app.py`
2. In the sidebar, select **Upload JSON**
3. Upload any `.json` file from `data/sample_data/`

### Programmatically
```python
from src.graph import Graph

g = Graph()
g.load_from_json("data/sample_data/urban_downtown.json")

print(g.get_node_count())   # 20
print(g.get_edge_count())   # 32
```

---

## How to Add a New Dataset

1. Create a new `.json` file under `data/sample_data/`
2. Follow the schema above. Use sequential `node_id` values starting from 0.
3. Make sure every `from_id` and `to_id` in edges references a valid `node_id`.
4. Do **not** include `final_weight` — it will be computed by the code.

### Naming convention
- Use lowercase with underscores: `neighborhood_name.json`

---

## real_locations/ folder

Reserved for future hand-crafted JSON files based on real-world locations.
Follow the same JSON schema — assign `x`, `y` as spatial coordinates and
`time_cost` based on real walking distances (~83 m/min walking speed).

---

## Phase 2 Note

Planned: allow users to override node/edge rewards per their dog's individual
preferences (e.g. a dog that dislikes dog parks). This will require a new
`update_node` method in `src/graph.py` and UI inputs in `app.py`.
The JSON schema will remain unchanged.
