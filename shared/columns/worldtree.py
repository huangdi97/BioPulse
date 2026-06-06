TABLE_NODE_MEMORY_LINKS_COLS = frozenset(
    {
        "id",
        "node_id",
        "memory_entry_id",
        "relevance_score",
        "created_at",
    }
)

TABLE_WORLD_TREE_NODES_COLS = frozenset(
    {
        "id",
        "name",
        "description",
        "parent_id",
        "path",
        "level",
        "node_type",
        "sort_order",
        "metadata",
        "is_active",
        "created_by",
        "created_at",
        "updated_at",
    }
)

TABLE_WORLD_TREE_SNAPSHOTS_COLS = frozenset(
    {
        "id",
        "node_id",
        "snapshot_type",
        "subtree_json",
        "memory_count",
        "version",
        "created_at",
        "expires_at",
    }
)
