import pytest

from cloud.app.services.agent_core import (
    CycleDetectedError,
    EDAGNode,
    PortTypeError,
)


class TestEDAGNodeCreation:
    def test_create_node_with_id(self) -> None:
        node = EDAGNode(id="test")
        assert node.id == "test"

    def test_create_node_with_ports(self) -> None:
        node = EDAGNode(id="calc", input_port={"x": int}, output_port={"y": str})
        assert node.input_port == {"x": int}
        assert node.output_port == {"y": str}

    def test_create_node_no_parent(self) -> None:
        node = EDAGNode(id="orphan")
        assert node.parent is None

    def test_create_node_empty_children(self) -> None:
        node = EDAGNode(id="leaf")
        assert node.children == []

    def test_unique_ids(self) -> None:
        n1 = EDAGNode(id="a")
        n2 = EDAGNode(id="b")
        assert n1.id != n2.id


class TestEDAGNodePortValidation:
    def test_validate_input_type_match(self) -> None:
        node = EDAGNode(id="n", input_port={"val": int})
        node.validate_input({"val": 42})

    def test_validate_input_type_mismatch_raises(self) -> None:
        node = EDAGNode(id="n", input_port={"val": int})
        with pytest.raises(PortTypeError, match="expects int, got str"):
            node.validate_input({"val": "not_a_number"})

    def test_validate_output_type_match(self) -> None:
        node = EDAGNode(id="n", output_port={"result": str})
        node.validate_output({"result": "ok"})

    def test_validate_output_type_mismatch_raises(self) -> None:
        node = EDAGNode(id="n", output_port={"result": str})
        with pytest.raises(PortTypeError, match="expects str, got int"):
            node.validate_output({"result": 42})

    def test_validate_input_missing_key_skips(self) -> None:
        node = EDAGNode(id="n", input_port={"val": int})
        node.validate_input({"other": "ignored"})

    def test_str_to_int_validation_raises(self) -> None:
        node = EDAGNode(id="n", input_port={"count": int})
        with pytest.raises(PortTypeError):
            node.validate_input({"count": "42"})


class TestEDAGNodeLinking:
    def test_add_child_sets_parent(self) -> None:
        parent = EDAGNode(id="parent")
        child = EDAGNode(id="child")
        parent.add_child(child)
        assert child.parent is parent

    def test_add_child_appends_to_children(self) -> None:
        parent = EDAGNode(id="parent")
        child = EDAGNode(id="child")
        parent.add_child(child)
        assert child in parent.children

    def test_add_multiple_children(self) -> None:
        parent = EDAGNode(id="parent")
        c1 = EDAGNode(id="c1")
        c2 = EDAGNode(id="c2")
        parent.add_child(c1)
        parent.add_child(c2)
        assert len(parent.children) == 2

    def test_grandchild_linking(self) -> None:
        root = EDAGNode(id="root")
        child = EDAGNode(id="child")
        grandchild = EDAGNode(id="grandchild")
        root.add_child(child)
        child.add_child(grandchild)
        assert grandchild.parent is child
        assert grandchild in child.children

    def test_isolated_node_parent_is_none(self) -> None:
        node = EDAGNode(id="alone")
        assert node.parent is None


class TestEDAGNodeCycleDetection:
    def test_direct_cycle_raises(self) -> None:
        a = EDAGNode(id="A")
        b = EDAGNode(id="B")
        a.add_child(b)
        with pytest.raises(CycleDetectedError, match="would create a cycle"):
            b.add_child(a)

    def test_indirect_cycle_raises(self) -> None:
        a = EDAGNode(id="A")
        b = EDAGNode(id="B")
        c = EDAGNode(id="C")
        a.add_child(b)
        b.add_child(c)
        with pytest.raises(CycleDetectedError):
            c.add_child(a)

    def test_self_cycle_raises(self) -> None:
        node = EDAGNode(id="self")
        with pytest.raises(CycleDetectedError):
            node.add_child(node)

    def test_no_cycle_with_unrelated_nodes(self) -> None:
        a = EDAGNode(id="A")
        b = EDAGNode(id="B")
        c = EDAGNode(id="C")
        a.add_child(b)
        a.add_child(c)
        assert len(a.children) == 2


class TestEDAGNodeTraversal:
    def test_dfs_single_node(self) -> None:
        node = EDAGNode(id="root")
        assert [n.id for n in node.dfs()] == ["root"]

    def test_dfs_order(self) -> None:
        root = EDAGNode(id="root")
        c1 = EDAGNode(id="c1")
        c2 = EDAGNode(id="c2")
        gc = EDAGNode(id="gc")
        root.add_child(c1)
        root.add_child(c2)
        c1.add_child(gc)
        assert [n.id for n in root.dfs()] == ["root", "c1", "gc", "c2"]

    def test_bfs_single_node(self) -> None:
        node = EDAGNode(id="root")
        assert [n.id for n in node.bfs()] == ["root"]

    def test_bfs_order(self) -> None:
        root = EDAGNode(id="root")
        c1 = EDAGNode(id="c1")
        c2 = EDAGNode(id="c2")
        gc = EDAGNode(id="gc")
        root.add_child(c1)
        root.add_child(c2)
        c1.add_child(gc)
        assert [n.id for n in root.bfs()] == ["root", "c1", "c2", "gc"]

    def test_dfs_with_edag_fixture(self, edag_node: EDAGNode) -> None:
        ids = [n.id for n in edag_node.dfs()]
        assert ids == ["root", "child1", "grandchild", "child2"]

    def test_bfs_with_edag_fixture(self, edag_node: EDAGNode) -> None:
        ids = [n.id for n in edag_node.bfs()]
        assert ids == ["root", "child1", "child2", "grandchild"]


class TestEDAGNodeSerialization:
    def test_to_dict_roundtrip(self, edag_node: EDAGNode) -> None:
        data = edag_node.to_dict()
        restored = EDAGNode.from_dict(data)
        assert restored.id == edag_node.id

    def test_from_dict_maintains_structure(self) -> None:
        data = {
            "id": "root",
            "input_port": {"x": "int"},
            "output_port": {"y": "str"},
            "children": [
                {
                    "id": "child",
                    "input_port": {},
                    "output_port": {},
                    "children": [],
                }
            ],
        }
        node = EDAGNode.from_dict(data)
        assert node.id == "root"
        assert node.input_port == {"x": int}
        assert node.output_port == {"y": str}
        assert len(node.children) == 1
        assert node.children[0].id == "child"
        assert node.children[0].parent is node

    def test_to_dict_serializes_types(self) -> None:
        node = EDAGNode(id="n", input_port={"val": float}, output_port={"ok": bool})
        data = node.to_dict()
        assert data["input_port"]["val"] == "float"
        assert data["output_port"]["ok"] == "bool"

    def test_from_dict_restores_types(self) -> None:
        data = {
            "id": "n",
            "input_port": {"val": "float"},
            "output_port": {"ok": "bool"},
            "children": [],
        }
        node = EDAGNode.from_dict(data)
        assert node.input_port["val"] is float
        assert node.output_port["ok"] is bool

    def test_from_dict_empty_ports(self) -> None:
        data = {"id": "n", "input_port": {}, "output_port": {}, "children": []}
        node = EDAGNode.from_dict(data)
        assert node.input_port == {}
        assert node.output_port == {}

    def test_serialize_deserialize_isolated_node(self) -> None:
        node = EDAGNode(id="alone")
        data = node.to_dict()
        restored = EDAGNode.from_dict(data)
        assert restored.id == "alone"
        assert restored.parent is None

    def test_serialize_deserialize_preserves_no_parent(self) -> None:
        node = EDAGNode(id="root")
        data = node.to_dict()
        restored = EDAGNode.from_dict(data)
        assert restored.parent is None
