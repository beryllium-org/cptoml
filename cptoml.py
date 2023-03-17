from storage import remount, getmount


def _rcm(line) -> str:
    """
    Remove comments from a line buffer.
    Also removes misc chars.
    """
    if line.rfind("#") != -1:  # Without the check -1 eats a char
        line = line[: line.rfind("#")]
    while line.endswith(" ") or line.endswith("\n"):
        line = line[:-1]
    while line.startswith(" "):
        line = line[1:]
    return line


def _df(data):
    """
    Prepares the data into a list.
    """
    data = data.split("\n")
    for i in range(len(data) - 1, 0, -1):  # Go in reverse as to not break the index
        if data[i].isspace() or not data[i]:  # "" == False
            data.pop(i)
    return data


def _ef(line):
    """
    Get the value out of a line.
    """
    result = _rcm(line)
    result = result[result.find("=") + 1 :]
    result = _rcm(result)  # for spaces

    if (result.startswith('"') and result.endswith('"')) or (
        result.startswith("'") and result.endswith("'")
    ):  # chars
        result = result[1:-1]
    elif result.isdigit() or (result[0] in ["-", "+"] and result[1:].isdigit()):  # ints
        result = int(result)
    elif result[0] == "0" and result[1].isletter():  # other numeric
        if result[1] == "x":  # hex
            result = hex(int(result[2:], 16))
        elif result[1] == "o":  # octal
            result = oct(int(result[2:], 8))
        elif result[0].isdigit() and ("e" in result):  # notation
            exec(f"result = int({result})")
        else:
            del line, result
            raise TypeError("Invalid value.")
    elif result == "true":  # bools
        result = True
    elif result == "false":
        result = False
    else:
        del line, result
        raise TypeError("Invalid value.")
    del line
    return result


def _lf(buf, key, start=0) -> int:
    """
    Find key buffer index.
    Use start to place into the correct table.

    Returns -1 when not found.
    """
    result = -1
    tm = start
    q = True
    while q:
        try:
            tml = _rcm(buf[tm])
        except IndexError:
            q = False
        if q and (tml.startswith(key + "=") or tml.startswith(key + " =")):
            result = tm
            q = False
        elif q and ((len(buf) == tm + 1) or tml.startswith("[")):
            q = False
        del tml
        tm += 1
        if not q:
            break
    del buf, start, key, tm, q
    return result


def _lm(key, value, comment=None) -> str:
    """
    Creates a new toml line with key and value.
    Accepts comment.
    """
    result = key + " = "
    if isinstance(value, str):
        result += '"' + value.replace("\n", "\\n") + '"'  # make raw
    elif isinstance(value, int) or isinstance(value, float):
        if str(value) != "inf":
            result += str(value)
        else:
            del result, key, value, comment
            raise TypeError("Value infinite")
    elif isinstance(value, bool):
        result += str(value).lower()
    else:
        del result, key, value, comment
        raise TypeError("Unsupported type for toml")
    if comment is not None:
        result += " # " + comment
    del key, value, comment
    return result


def _ap(data) -> list:
    """
    Apply formatting.

    - Spaces it out subtables.
    - Removes blank tables.
    """
    bb = False  # Back to back subtable decleration
    el = False  # no element in subtable
    for i in range(len(data) - 1, 0, -1):
        if data[i].startswith("["):
            if (bb is False) and el:
                bb = True
                el = False
                data.insert(i, "")
            else:  # The current subtable should be removed!
                data.pop(i)
                # Should remain true.
        else:
            if bb:
                bb = False
            if not el:
                el = True
    del bb, el
    return data


def _tf(buf, subtable) -> int:
    """
    Find subtable buffer index.

    Returns -1 when not found.
    """
    result = -1
    tm = 0
    q = True
    while q:
        tml = None
        try:
            tml = _rcm(buf[tm])
        except IndexError:
            q = False
        if q and tml.startswith("[") and (tml == f"[{subtable}]"):
            result = tm
            q = False
        del tml
        tm += 1
        if not q:
            break
    del buf, subtable, tm, q
    return result


def fetch(item, subtable=None, toml="/settings.toml"):
    if not isinstance(item, str):
        del item, subtable, toml
        raise TypeError("Item should be str.")
    if subtable is not None and not isinstance(subtable, str):
        del item, subtable, toml
        raise TypeError("Subtable should be str.")
    try:
        with open(toml) as tomlf:
            data = _df(tomlf.read())  # load into list
            result = None
            if subtable is None:  # Browse root table
                target = _lf(data, item)
                if target != -1:
                    result = _ef(data[target])
            else:
                start = _tf(data, subtable)  # find table offset
                if start != -1:
                    start += 1
                if start != -1:  # table found
                    tr = _lf(data, item, start)  # fetch item index
                    if tr != -1:
                        result = _ef(data[tr])  # load value
                    del tr
                del start
            del data, subtable, toml, item
            return result
    except OSError:
        del item, subtable, toml
        raise OSError("Toml file not found")


def put(item, value, subtable=None, toml="/settings.toml", comment=None) -> None:
    """
    Store / Update a value. You can also place a comment.

    The existing comment will be removed.
    """
    data = None
    ro = False

    try:
        with open(toml) as tomlr:
            data = _df(tomlr.read())
    except OSError:
        raise OSError("Toml file not found")
    if data is not None:
        # Find target line
        start = 0
        if subtable is not None:
            start = _tf(data, subtable)  # find table offset
        if start == -1:  # Need to create new subtable
            data.append(f"[{subtable}]")
            data.append(_lm(item, value, comment))
        else:  # Whatever start says
            tr = _lf(data, item, start + 1)  # fetch item index
            if tr == -1:  # New key
                data.insert(start + 1, _lm(item, value, comment))
            else:  # Existing key
                data[tr] = _lm(item, value, comment)
        del start

        # Reapply formatting
        data = _ap(data)

        # Write to file
        with open(toml, "w") as tomlw:
            for line in data:
                tomlw.write(f"{line}\n")
                del line
    del item, value, subtable, toml, comment, data, ro


def delete(item, subtable=None, toml="/settings.toml") -> None:
    """
    Delete an entry on the toml file.
    """
    data = None
    try:
        with open(toml) as tomlr:
            data = _df(tomlr.read())
    except OSError:
        raise OSError("Toml file not found")
    if data is not None:
        # Find target line
        start = 0
        if subtable is not None:
            start = _tf(data, subtable)  # find table offset
        if start != -1:
            tr = _lf(data, item, start + 1)  # fetch item index
            if tr != -1:
                data.pop(tr)
        del start

        # Reapply formatting
        data = _ap(data)

        # Write to file
        with open(toml, "w") as tomlw:
            for line in data:
                tomlw.write(f"{line}\n")
                del line
    del item, subtable, toml, data
