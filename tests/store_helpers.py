"""Locate HA's prepared-data file writer, whose home moved in Home Assistant 2026.11."""


def store_writer(store):
    """Return (owner, attribute) of the writer taking (mode, json_data)."""
    if (file_io := getattr(store, "_io", None)) is not None:
        return file_io, "_write"
    return store, "_write_prepared_data"
