# Spec review

Plain-English mapping:
- `parent_equals_sum_of_children_spec`: each internal node equals the sum of its direct children.
- `root_equals_sum_of_leaves_spec`: the root stores the total stake across all leaves.
- `draw_interval_matches_weights_spec`: ticket intervals assigned by the draw routine match the leaves' weights.
- `draw_selects_valid_leaf`: any in-range draw must end at one of the four leaf indices in the benchmark tree.
- `node_id_bijection_spec`: node-index and stake-path mappings remain mutually consistent.

Why this matches the intended property:
- The real library's critical behavior is additive parent maintenance plus weighted traversal during draw.
- The fixed four-leaf slice preserves that logic in a form suitable for benchmark tasks.

Known uncertainties:
- The benchmark specializes the dynamic tree into a fixed binary shape.
- The probabilistic claim is represented as interval ownership, not as an external probability theorem.
