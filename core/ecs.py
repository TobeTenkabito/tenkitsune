from typing import Type, TypeVar, Dict, Any
import uuid

T = TypeVar('T')

class World:
    """管理所有實體和組件"""
    def __init__(self):
        self._components: Dict[int, Dict[type, Any]] = {}
        self._next_id = 0

    def create_entity(self) -> int:
        eid = self._next_id
        self._next_id += 1
        self._components[eid] = {}
        return eid

    def add_component(self, entity_id: int, component):
        self._components[entity_id][type(component)] = component

    def get_component(self, entity_id: int, component_type: Type[T]) -> T | None:
        return self._components.get(entity_id, {}).get(component_type)

    def has_component(self, entity_id: int, component_type: type) -> bool:
        return component_type in self._components.get(entity_id, {})

    def query(self, *component_types: type) -> list[int]:
        """查詢擁有所有指定組件的實體"""
        result = []
        for eid, comps in self._components.items():
            if all(ct in comps for ct in component_types):
                result.append(eid)
        return result

    def destroy_entity(self, entity_id: int):
        self._components.pop(entity_id, None)


# 全局世界
world = World()
