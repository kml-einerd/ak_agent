"""Tests for the atomic decorator and registry."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from atomic import atomic, AtomicRegistry, ParamMeta, AtomicMeta


class TestAtomicDecorator:
    """Test the @atomic() decorator."""

    def setup_method(self):
        AtomicRegistry.clear()

    def test_basic_registration(self):
        @atomic(group="test", title="My Func")
        def my_func(name: str):
            """Docstring here."""
            return f"hello {name}"

        assert "test.my_func" in AtomicRegistry.list_keys()

    def test_introspection_params(self):
        @atomic(group="g")
        def func_with_params(required_str: str, optional_int: int = 42, flag: bool = False):
            """Does stuff."""
            pass

        meta = AtomicRegistry.get("g.func_with_params")
        assert meta is not None
        assert len(meta.inputs) == 3

        # required_str should be required
        p0 = meta.inputs[0]
        assert p0.key == "required_str"
        assert p0.type == "string"
        assert p0.required is True

        # optional_int should have default
        p1 = meta.inputs[1]
        assert p1.key == "optional_int"
        assert p1.type == "integer"
        assert p1.required is False
        assert p1.default == 42

        # flag should be bool
        p2 = meta.inputs[2]
        assert p2.type == "boolean"
        assert p2.default is False

    def test_docstring_extraction(self):
        @atomic(group="doc")
        def documented():
            """This is the description."""
            pass

        meta = AtomicRegistry.get("doc.documented")
        assert meta.description == "This is the description."

    def test_depends_on(self):
        @atomic(group="a", depends_on=["b.other"])
        def dependent():
            pass

        meta = AtomicRegistry.get("a.dependent")
        assert meta.depends_on == ["b.other"]

    def test_run_executes_function(self):
        @atomic(group="run")
        def adder(x: int = 0, y: int = 0):
            return x + y

        result = AtomicRegistry.run("run.adder", x=3, y=7)
        assert result == 10

    def test_run_applies_defaults(self):
        @atomic(group="run")
        def greeter(name: str = "world"):
            return f"hello {name}"

        result = AtomicRegistry.run("run.greeter")
        assert result == "hello world"

    def test_run_missing_key_raises(self):
        with pytest.raises(KeyError):
            AtomicRegistry.run("nonexistent.func")

    def test_wrapper_preserves_name(self):
        @atomic(group="w")
        def original_name():
            pass

        assert original_name.__name__ == "original_name"

    def test_atomic_meta_attached(self):
        @atomic(group="m", title="Attached")
        def has_meta():
            pass

        assert hasattr(has_meta, "_atomic_meta")
        assert has_meta._atomic_meta.title == "Attached"


class TestAtomicJSON:
    """Test JSON Schema generation."""

    def setup_method(self):
        AtomicRegistry.clear()

    def test_json_schema_structure(self):
        @atomic(group="schema", title="Test Op", model="sonnet", acceptance="tests pass")
        def test_op(text: str, count: int = 5):
            """Test operation."""
            pass

        schema = AtomicRegistry.json()
        assert "schema.test_op" in schema

        entry = schema["schema.test_op"]
        assert entry["title"] == "Test Op"
        assert entry["model"] == "sonnet"
        assert entry["acceptance"] == "tests pass"
        assert entry["description"] == "Test operation."

        inputs = entry["inputSchema"]
        assert inputs["type"] == "object"
        assert "text" in inputs["properties"]
        assert inputs["properties"]["text"]["type"] == "string"
        assert inputs["properties"]["count"]["default"] == 5
        assert "text" in inputs["required"]
        assert "count" not in inputs["required"]

    def test_to_subwaves(self):
        @atomic(group="sw", title="Wave 1", model="haiku", depends_on=["sw.wave_0"])
        def wave_1():
            pass

        @atomic(group="sw", title="Wave 0", model="haiku")
        def wave_0():
            pass

        subwaves = AtomicRegistry.to_subwaves(group="sw")
        assert len(subwaves) == 2

        sw1 = [s for s in subwaves if s["id"] == "sw-sw-wave_1"][0]
        assert sw1["depends_on"] == ["sw.wave_0"]
        assert sw1["model"] == "haiku"

    def test_to_subwaves_filter_by_group(self):
        @atomic(group="a")
        def in_a():
            pass

        @atomic(group="b")
        def in_b():
            pass

        assert len(AtomicRegistry.to_subwaves(group="a")) == 1
        assert len(AtomicRegistry.to_subwaves(group="b")) == 1
        assert len(AtomicRegistry.to_subwaves()) == 2


class TestAtomicListType:
    """Test list/dict type introspection."""

    def setup_method(self):
        AtomicRegistry.clear()

    def test_list_type(self):
        @atomic(group="types")
        def with_list(items: list = None):
            pass

        meta = AtomicRegistry.get("types.with_list")
        assert meta.inputs[0].type == "array"

    def test_dict_type(self):
        @atomic(group="types")
        def with_dict(data: dict = None):
            pass

        meta = AtomicRegistry.get("types.with_dict")
        assert meta.inputs[0].type == "object"
