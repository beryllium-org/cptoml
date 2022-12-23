from gc import collect as _collect


def _elementfetch(line, item):
    if line.endswith("\n"):  # remove dangling \n
        line = line[:-1]

    result = line[line.find("=") + 1 :]

    while result.startswith(" "):  # remove unused spaces
        result = result[1:]

    if "#" in result:  # remove commends
        result = result[: result.rfind('"') + 1]

    if result.startswith('"') and result.endswith('"'):
        result = result[1:-1]
    elif result.isdigit() or (result[0] == "-" and result[1:].isdigit()):
        result = int(result)
    elif result[0] == "0" and result[1].isletter():
        if result[1] == "x":
            result = hex(int(result[2:], 16))
        elif result[1] == "o":
            result = oct(int(result[2:], 8))
        else:
            del line, item, result
            _collect()
            raise TypeError("Invalid value.")
    else:
        del line, item, result
        _collect()
        raise TypeError("Invalid value.")
    del line, item
    _collect()
    return result


def fetch(item, subtable=None, toml="/settings.toml"):
    if not isinstance(item, str):
        del item, subtable, toml
        raise TypeError("Item should be str.")
    if subtable is not None and not isinstance(subtable, str):
        del item, subtable, toml
        raise TypeError("Subtable should be str.")
    try:
        with open(toml, "r") as tomlf:
            result = None
            if subtable is None:  # Browse root table
                for line in tomlf:
                    if not line.startswith("["):
                        if line.startswith(item + "=") or line.startswith(item + " ="):
                            result = _elementfetch(line, item)
                        else:
                            del line
                    else:  # We have reached a subtable
                        del line
                        break
            else:  # crawl to specified table
                got = False
                for line in tomlf:
                    if not got:
                        if line.startswith("[") and line == f"[{subtable}]\n":
                            # It should always end with \n
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
