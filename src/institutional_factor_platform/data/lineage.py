"""Deterministic artifact lineage graph."""

from dataclasses import dataclass, field

from institutional_factor_platform.exceptions import ManifestError


@dataclass(slots=True)
class LineageGraph:
    parents: dict[str, set[str]] = field(default_factory=dict)

    def add(self, artifact_id: str, parent_ids: tuple[str, ...] = ()) -> None:
        if artifact_id in parent_ids:
            raise ManifestError("An artifact cannot be its own parent.")
        self.parents.setdefault(artifact_id, set()).update(parent_ids)
        if self._has_cycle(artifact_id, artifact_id, set()):
            self.parents[artifact_id].difference_update(parent_ids)
            raise ManifestError("Lineage relationship would create a cycle.")

    def ancestors(self, artifact_id: str) -> tuple[str, ...]:
        found: set[str] = set()
        stack = list(self.parents.get(artifact_id, set()))
        while stack:
            item = stack.pop()
            if item not in found:
                found.add(item)
                stack.extend(self.parents.get(item, set()))
        return tuple(sorted(found))

    def _has_cycle(self, current: str, target: str, visited: set[str]) -> bool:
        for parent in self.parents.get(current, set()):
            if parent == target:
                return True
            if parent not in visited:
                visited.add(parent)
                if self._has_cycle(parent, target, visited):
                    return True
        return False
