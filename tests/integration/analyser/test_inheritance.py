"""Integration tests for class inheritance across modules in Neo4j."""

from pathlib import Path

from mapper import analyser, graph_loader


class TestInheritance:
    """Tests for class inheritance tracking."""

    def test_single_inheritance(self, neo4j_connection, tmp_path: Path):
        """Test simple single inheritance relationship."""
        test_module = tmp_path / "test_module.py"
        test_module.write_text(
            """
class Parent:
    \"\"\"Parent class.\"\"\"
    def parent_method(self):
        \"\"\"Parent method.\"\"\"
        pass

class Child(Parent):
    \"\"\"Child class.\"\"\"
    def child_method(self):
        \"\"\"Child method.\"\"\"
        pass
"""
        )

        loader = graph_loader.GraphLoader(neo4j_connection, package_name="test_single")
        loader.clear_package()
        code_analyser = analyser.Analyser(tmp_path, loader=loader)
        result = code_analyser.analyse()

        assert result.success is True

        with neo4j_connection.driver.session(database=neo4j_connection.database) as session:
            # Verify both classes exist
            classes = session.run(
                """
                MATCH (c:Class {package: $pkg})
                RETURN c.name as name
                ORDER BY name
                """,
                pkg="test_single",
            ).data()

            assert len(classes) == 2
            assert classes[0]["name"] == "Child"
            assert classes[1]["name"] == "Parent"

            # Verify INHERITS relationship
            inherits = session.run(
                """
                MATCH (child:Class {package: $pkg})-[:INHERITS]->(parent:Class)
                RETURN child.name as child, parent.name as parent
                """,
                pkg="test_single",
            ).data()

            assert len(inherits) == 1
            assert inherits[0]["child"] == "Child"
            assert inherits[0]["parent"] == "Parent"

        loader.clear_package()

    def test_inheritance_chain(self, neo4j_connection, tmp_path: Path):
        """Test inheritance chain A -> B -> C."""
        test_module = tmp_path / "test_module.py"
        test_module.write_text(
            """
class GrandParent:
    \"\"\"Grand parent class.\"\"\"
    pass

class Parent(GrandParent):
    \"\"\"Parent class.\"\"\"
    pass

class Child(Parent):
    \"\"\"Child class.\"\"\"
    pass
"""
        )

        loader = graph_loader.GraphLoader(neo4j_connection, package_name="test_chain")
        loader.clear_package()
        code_analyser = analyser.Analyser(tmp_path, loader=loader)
        result = code_analyser.analyse()

        assert result.success is True

        with neo4j_connection.driver.session(database=neo4j_connection.database) as session:
            # Verify inheritance chain
            inherits = session.run(
                """
                MATCH (child:Class {package: $pkg})-[:INHERITS]->(parent:Class)
                RETURN child.name as child, parent.name as parent
                ORDER BY child
                """,
                pkg="test_chain",
            ).data()

            assert len(inherits) == 2
            # Child -> Parent
            assert inherits[0]["child"] == "Child"
            assert inherits[0]["parent"] == "Parent"
            # Parent -> GrandParent
            assert inherits[1]["child"] == "Parent"
            assert inherits[1]["parent"] == "GrandParent"

        loader.clear_package()

    def test_cross_module_inheritance(self, neo4j_connection, tmp_path: Path):
        """Test inheritance where base and derived are in different modules."""
        # Base module
        base_module = tmp_path / "base.py"
        base_module.write_text(
            """
class Vehicle:
    \"\"\"Base vehicle class.\"\"\"
    def move(self):
        \"\"\"Move vehicle.\"\"\"
        pass
"""
        )

        # Derived module
        derived_module = tmp_path / "derived.py"
        derived_module.write_text(
            """
from cross_mod.base import Vehicle

class Car(Vehicle):
    \"\"\"Car class.\"\"\"
    def drive(self):
        \"\"\"Drive car.\"\"\"
        pass
"""
        )

        loader = graph_loader.GraphLoader(neo4j_connection, package_name="cross_mod")
        loader.clear_package()
        code_analyser = analyser.Analyser(tmp_path, loader=loader)
        result = code_analyser.analyse()

        assert result.success is True

        with neo4j_connection.driver.session(database=neo4j_connection.database) as session:
            # Verify cross-module inheritance
            inherits = session.run(
                """
                MATCH (car:Class {package: $pkg, name: 'Car'})-[:INHERITS]->(vehicle:Class {name: 'Vehicle'})
                RETURN car.fqn as car_fqn, vehicle.fqn as vehicle_fqn
                """,
                pkg="cross_mod",
            ).data()

            assert len(inherits) == 1
            assert inherits[0]["car_fqn"] == "derived.Car"
            assert inherits[0]["vehicle_fqn"] == "base.Vehicle"

        loader.clear_package()

    def test_multiple_inheritance(self, neo4j_connection, tmp_path: Path):
        """Test class inheriting from multiple base classes."""
        test_module = tmp_path / "test_module.py"
        test_module.write_text(
            """
class Mixin1:
    \"\"\"First mixin.\"\"\"
    pass

class Mixin2:
    \"\"\"Second mixin.\"\"\"
    pass

class Combined(Mixin1, Mixin2):
    \"\"\"Combined class with multiple inheritance.\"\"\"
    pass
"""
        )

        loader = graph_loader.GraphLoader(neo4j_connection, package_name="test_multi")
        loader.clear_package()
        code_analyser = analyser.Analyser(tmp_path, loader=loader)
        result = code_analyser.analyse()

        assert result.success is True

        with neo4j_connection.driver.session(database=neo4j_connection.database) as session:
            # Verify multiple INHERITS relationships
            inherits = session.run(
                """
                MATCH (combined:Class {package: $pkg, name: 'Combined'})-[:INHERITS]->(base:Class)
                RETURN base.name as base_name
                ORDER BY base_name
                """,
                pkg="test_multi",
            ).data()

            assert len(inherits) == 2
            assert inherits[0]["base_name"] == "Mixin1"
            assert inherits[1]["base_name"] == "Mixin2"

        loader.clear_package()

    def test_inheritance_with_methods(self, neo4j_connection, tmp_path: Path):
        """Test that inherited methods are tracked correctly."""
        test_module = tmp_path / "test_module.py"
        test_module.write_text(
            """
class Base:
    \"\"\"Base class.\"\"\"
    def base_method(self):
        \"\"\"Base method.\"\"\"
        return "base"

class Derived(Base):
    \"\"\"Derived class.\"\"\"
    def derived_method(self):
        \"\"\"Derived method.\"\"\"
        return "derived"

    def override_method(self):
        \"\"\"Override method.\"\"\"
        return "overridden"
"""
        )

        loader = graph_loader.GraphLoader(neo4j_connection, package_name="test_methods")
        loader.clear_package()
        code_analyser = analyser.Analyser(tmp_path, loader=loader)
        result = code_analyser.analyse()

        assert result.success is True

        with neo4j_connection.driver.session(database=neo4j_connection.database) as session:
            # Verify inheritance exists
            inherits = session.run(
                """
                MATCH (derived:Class {package: $pkg})-[:INHERITS]->(base:Class)
                RETURN derived.name as derived, base.name as base
                """,
                pkg="test_methods",
            ).data()

            assert len(inherits) == 1

            # Verify methods are tracked
            methods = session.run(
                """
                MATCH (c:Class {package: $pkg})-[:CONTAINS]->(m:Method)
                RETURN c.name as class_name, m.name as method_name
                ORDER BY class_name, method_name
                """,
                pkg="test_methods",
            ).data()

            # Base has 1 method, Derived has 2 methods
            base_methods = [m for m in methods if m["class_name"] == "Base"]
            derived_methods = [m for m in methods if m["class_name"] == "Derived"]

            assert len(base_methods) == 1
            assert base_methods[0]["method_name"] == "base_method"

            assert len(derived_methods) == 2
            assert derived_methods[0]["method_name"] == "derived_method"
            assert derived_methods[1]["method_name"] == "override_method"

        loader.clear_package()

    def test_inheritance_diamond_pattern(self, neo4j_connection, tmp_path: Path):
        """Test diamond inheritance pattern (A <- B, A <- C, B <- D, C <- D)."""
        test_module = tmp_path / "test_module.py"
        test_module.write_text(
            """
class A:
    \"\"\"Top of diamond.\"\"\"
    pass

class B(A):
    \"\"\"Left branch.\"\"\"
    pass

class C(A):
    \"\"\"Right branch.\"\"\"
    pass

class D(B, C):
    \"\"\"Bottom of diamond.\"\"\"
    pass
"""
        )

        loader = graph_loader.GraphLoader(neo4j_connection, package_name="test_diamond")
        loader.clear_package()
        code_analyser = analyser.Analyser(tmp_path, loader=loader)
        result = code_analyser.analyse()

        assert result.success is True

        with neo4j_connection.driver.session(database=neo4j_connection.database) as session:
            # Verify all inheritance relationships
            inherits = session.run(
                """
                MATCH (child:Class {package: $pkg})-[:INHERITS]->(parent:Class)
                RETURN child.name as child, parent.name as parent
                ORDER BY child, parent
                """,
                pkg="test_diamond",
            ).data()

            # B->A, C->A, D->B, D->C
            assert len(inherits) == 4

            # Check specific relationships
            b_to_a = any(i["child"] == "B" and i["parent"] == "A" for i in inherits)
            c_to_a = any(i["child"] == "C" and i["parent"] == "A" for i in inherits)
            d_to_b = any(i["child"] == "D" and i["parent"] == "B" for i in inherits)
            d_to_c = any(i["child"] == "D" and i["parent"] == "C" for i in inherits)

            assert b_to_a
            assert c_to_a
            assert d_to_b
            assert d_to_c

        loader.clear_package()
