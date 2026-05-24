from __future__ import annotations

from importlib import import_module

_MODULE_NAMES = [
    "_base",
    "_accounting_questions",
    "_source_models",
    "_actions",
    "_piece_workshop",
    "_summaries",
    "_comptes_fields",
    "_comptes_common",
    "_comptes_builder",
    "_registre_helpers",
    "_registre_items",
    "_registre_model",
    "_pieces_ux",
    "_priority_views",
    "_memoire_helpers",
    "_memoire_model",
    "_passation",
    "_ux_model",
    "_exports",
    "_dashboard",
]

_modules = [import_module(f"{__name__}.{module_name}") for module_name in _MODULE_NAMES]
_namespace: dict[str, object] = {}
for module in _modules:
    _namespace.update(
        {
            name: value
            for name, value in module.__dict__.items()
            if name not in {"annotations"} and not name.startswith("__")
        }
    )
for module in _modules:
    module.__dict__.update(_namespace)

globals().update(_namespace)
__all__ = sorted(name for name in _namespace if name not in {"annotations"})
