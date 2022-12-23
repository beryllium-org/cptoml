from gc import collect as _collect


def _elementfetch(line, item):
    result = line[len(item) + 1 :]
    if result.startswith('"') and result.endswith('"'):
        result = result[1:-1]
    elif result.isdigit():
        pass  # Nothing to do, this is needed though
    else:
        del line, item, result
        raise TypeError("Invalid value.")
    del line, item
    _collect()
    return result


def fetch(item, subtable=None, toml="/settings.toml"):
    if not isinstance(item, str):
        del item, subtable, toml
        raise TypeError("Item should be str.")
    if not isinstance(subtable, str):
        del item, subtable, toml
        raise TypeError("Subtable should be str.")
    try:
        with open(toml, "r") as toml:
            result = None
            if subtable is None:  # Browse root table
                for line in toml:
                    if not line.startswith("["):
                        if line.startswith(item + "="):
                            result = _elementfetch(line, item)
                        else:
                            del line
                    else:  # We have reached a subtable
                        del line
                        break
            else:  # crawl to specified table
                got = False
                for line in toml:
                    if not got:
                        if line.startswith("[") and line == f"[{subtable}]":
                            got = True  # we have reached the desired point
                            del line
                        else:
                            del line
                    elif line.startswith(item + "="):
                        result = _elementfetch(line, item)
                    else:
                        del line
                del got
            _collect()
            return result
    except OSError:
        del item, subtable, toml
        _collect()
        raise OSError("Toml file not found")


def put(item, value, subtable=None, toml="/settings.toml", comment=None):
    del item, value, subtable, toml, comment
