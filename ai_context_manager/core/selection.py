"""
Strict data model for handling file selections via JSON Schema.
"""
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Any, Optional

import jsonschema
import yaml

SCHEMA_PATH = Path(__file__).parent.parent / "schemas" / "context-definition.schema.json"


@dataclass
class SelectionMeta:
    description: str
    createdAt: str
    createdBy: str
    updatedAt: str
    updatedBy: str
    documentType: str
    tags: List[str] = field(default_factory=list)
    version: Optional[str] = None


@dataclass
class Selection:
    base_path: Path
    include_paths: List[Path]
    meta: SelectionMeta

    @classmethod
    def load(cls, yaml_path: Path) -> "Selection":
        """
        Load selection from a YAML file with strict Schema validation.
        No legacy support.
        """
        if not yaml_path.exists():
            raise FileNotFoundError(f"Selection file not found: {yaml_path}")

        try:
            with open(yaml_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
        except Exception as exc:
            raise ValueError(f"Failed to parse YAML: {exc}") from exc

        cls._validate_schema(data)

        content = data["content"]
        raw_base = content["basePath"]
        if Path(raw_base).is_absolute():
            base = Path(raw_base).resolve()
        else:
            base = (yaml_path.parent / raw_base).resolve()

        includes = content.get("include", [])
        include_paths = [base / p for p in includes]

        meta_dict = data["meta"]
        meta = SelectionMeta(
            description=meta_dict["description"],
            createdAt=meta_dict["createdAt"],
            createdBy=meta_dict["createdBy"],
            updatedAt=meta_dict["updatedAt"],
            updatedBy=meta_dict["updatedBy"],
            documentType=meta_dict["documentType"],
            tags=meta_dict.get("tags", []),
            version=meta_dict.get("version"),
        )

        return cls(base_path=base, include_paths=include_paths, meta=meta)

    @staticmethod
    def _validate_schema(data: Dict[str, Any]) -> None:
        """Validate data against the JSON schema."""
        if not SCHEMA_PATH.exists():
            raise RuntimeError("Internal Error: Schema definition file missing.")

        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        try:
            jsonschema.validate(instance=data, schema=schema)
        except jsonschema.ValidationError as exc:
            path = " -> ".join(str(p) for p in exc.path) if exc.path else "root"
            raise ValueError(f"Schema Validation Error at '{path}': {exc.message}") from exc

    def resolve_all_files(self) -> List[Path]:
        """
        Flatten the selection into a distinct list of files.
        Checks filesystem to determine if a path is a file or directory.
        """
        final_list: List[Path] = []

        for path in self.include_paths:
            if not path.exists():
                continue

            if path.is_file():
                final_list.append(path)
            elif path.is_dir():
                for file_path in path.rglob("*"):
                    if file_path.is_file():
                        final_list.append(file_path)

        return sorted(list(set(final_list)))
