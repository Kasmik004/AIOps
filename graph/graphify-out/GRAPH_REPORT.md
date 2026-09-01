# Graph Report - graph  (2026-09-01)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 16 nodes · 15 edges · 6 communities (1 shown, 5 thin omitted)
- Extraction: 100% EXTRACTED · 0% INFERRED · 0% AMBIGUOUS
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `1eae1f60`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- code_server.py
- test.py
- delete_item
- patch_item
- create_item
- update_item

## God Nodes (most connected - your core abstractions)
1. `AgentState` - 2 edges
2. `get_items()` - 2 edges
3. `read_root()` - 2 edges
4. `delete_item()` - 2 edges
5. `patch_item()` - 2 edges
6. `create_item()` - 2 edges
7. `update_item()` - 2 edges

## Surprising Connections (you probably didn't know these)
- None detected - all connections are within the same source files.

## Import Cycles
- None detected.

## Communities (6 total, 5 thin omitted)

### Community 1 - "test.py"
Cohesion: 0.67
Nodes (3): get, get_items(), read_root()

## Knowledge Gaps
- **5 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `delete_item()` connect `delete_item` to `test.py`?**
  _High betweenness centrality (0.095) - this node is a cross-community bridge._
- **Why does `patch_item()` connect `patch_item` to `test.py`?**
  _High betweenness centrality (0.095) - this node is a cross-community bridge._
- **Why does `create_item()` connect `create_item` to `test.py`?**
  _High betweenness centrality (0.095) - this node is a cross-community bridge._