"""Turn a nested fighter record into flat columns, e.g.

    fighter_stats.striking_stats.sig_str_by_target.head -> striking_sig_str_by_target_head
    records.wins                                        -> wins
"""
from .items import FighterBioItem

# Container names that add nothing to a column name, or a shorter form.
PREFIXES = {
    "records": "",
    "fighter_stats": "",
    "striking_stats": "striking",
    "grappling_stats": "grappling",
}


def _column(path):
    parts = [PREFIXES.get(part, part) for part in path]
    return "_".join(part for part in parts if part)


def _declared_order(item_class):
    """Field names in the order they're written in items.py.

    Item.fields is alphabetical; Scrapy keeps the original class body on
    `_class`. Fall back to alphabetical if that ever goes away.
    """
    declared = [n for n in vars(getattr(item_class, "_class", object)) if n in item_class.fields]
    return declared if len(declared) == len(item_class.fields) else list(item_class.fields)


def _paths(item_class, prefix=()):
    for name in _declared_order(item_class):
        nested = item_class.fields[name].get("nested")
        if nested:
            yield from _paths(nested, prefix + (name,))
        else:
            yield prefix + (name,)


def _flat_fields():
    fields = [_column(path) for path in _paths(FighterBioItem)]
    duplicates = {f for f in fields if fields.count(f) > 1}
    assert not duplicates, f"flattened column names collide: {duplicates}"
    return fields


# Every column, in a stable order (bio first, then records, then stats).
FLAT_FIELDS = _flat_fields()


def flatten(item, prefix=()):
    flat = {}
    for key, value in dict(item).items():
        if isinstance(value, dict):
            flat.update(flatten(value, prefix + (key,)))
        else:
            flat[_column(prefix + (key,))] = value
    return flat
