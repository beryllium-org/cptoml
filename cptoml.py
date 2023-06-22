class InvalidTOMLSyntax(Exception):
    """Custom class for bad syntax."""
    pass

def _prepareline(line: str) -> str:
    """
    Remove comments from a line buffer.
    Also removes misc chars.
    """

    # strip takes a string as argument it will remove any char on it
    # from the head and tail of input string
    _CHARS_TO_REMOVE = " \n"

    # first cleanup
    line = line.strip(_CHARS_TO_REMOVE)

    # check for string
    string_start = min(line.find("'"), line.find('"'))

    # no string
    if string_start == -1:
        return line[:line.find("#")].strip(_CHARS_TO_REMOVE)

    # TODO: Ensure string is after '='
    # string
    string_delimiter = line[string_start]
    if line.count(string_delimiter != 2):
        raise InvalidTOMLSyntax("Malformed string")

    # end of line (after the string quotes)
    string_end = line.rfind(string_delimiter)
    end_line = line[string_end+1:]

    # remove comment
    comment_start = end_line.find("#")
    
    # check if there's still something
    if end_line[:comment_start].strip(_CHARS_TO_REMOVE):
        raise InvalidTOMLSyntax("Content after string has ended")

    return line[:string_end+1].strip(_CHARS_TO_REMOVE)



def _dataformat(data: str) -> list[str]:
    """Prepares the data into a list."""
    return [d for d in data.split("\n") if d and not d.isspace()]


def _linevalue(line: str) -> Any:
    """Get the value out of a line."""
    result = _prepareline(line)
    result = result[result.find("=") + 1 :]
    result = _prepareline(result)  # for spaces

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


def _linefind(buf, key, start=0) -> int:
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
            tml = _prepareline(buf[tm])
        except IndexError:
            q = False
        if q and (tml.startswith(f"{key}=") or tml.startswith(f"{key} =")):
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


def _linemake(key, value, comment=None) -> str:
    """
    Creates a new toml line with key and value.
    Accepts comment.
    """
    result = f"{key} = "
    if isinstance(value, str):
        result += '"' + value.replace("\n", "\\n") + '"'  # make raw
    elif isinstance(value, (int, float)):
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
        result += f" # {comment}"
    del key, value, comment
    return result


def _applyformatting(data) -> list:
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


def _tablefind(buf, subtable) -> int:
    """
    Find subtable buffer index.

    Returns -1 when not found.
    """

    for index, line in enumerate(buf):
        try:
            tml = _prepareline(line)

            if tml == f"[{subtable}]":
                return index

        except IndexError:
            break

    del buf, subtable
    return -1


def _getkeys(buf, start=0):
    """
    Get the keys off a table.
    """
    res = []
    tm = start
    for index, line in enumerate(buf, start):
        tml = None
        try:
            tml = _prepareline(line)
            
            if tml.startswith("["):
                break
            
            if "=" in tml:
                tml = tml[: tml.find("=")]
                res.append(tml.rstrip())

        except IndexError:
            break

    del buf, start
    return res


def keys(subtable=None, toml="/settings.toml"):
    try:
        with open(toml) as tomlf:
            data = _dataformat(tomlf.read())  # load into list
            result = []
            if subtable is None:  # Browse root table
                result += _getkeys(data)  # fetch keys
            else:
                start = _tablefind(data, subtable)  # find table offset
                if start != -1:  # table found
                    result += _getkeys(data, start + 1)  # fetch keys
                del start
            del data, subtable, toml
            return result
    except OSError:
        del item, subtable, toml
        raise OSError("Toml file not found")


def fetch(item, subtable=None, toml="/settings.toml"):
    if not isinstance(item, str):
        del item, subtable, toml
        raise TypeError("Item should be str.")
    if subtable is not None and not isinstance(subtable, str):
        del item, subtable, toml
        raise TypeError("Subtable should be str.")
    try:
        with open(toml) as tomlf:
            data = _dataformat(tomlf.read())  # load into list
            result = None
            if subtable is None:  # Browse root table
                target = _linefind(data, item)
                if target != -1:
                    result = _linevalue(data[target])
            else:
                start = _tablefind(data, subtable)  # find table offset
                if start != -1:
                    start += 1
                if start != -1:  # table found
                    tr = _linefind(data, item, start)  # fetch item index
                    if tr != -1:
                        result = _linevalue(data[tr])  # load value
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
            data = _dataformat(tomlr.read())
    except OSError:
        raise OSError("Toml file not found")
    if data is not None:
        # Find target line
        start = 0
        if subtable is not None:
            start = _tablefind(data, subtable)  # find table offset
        if start == -1:  # Need to create new subtable
            data.append(f"[{subtable}]")
            data.append(_linemake(item, value, comment))
        else:  # Whatever start says
            tr = _linefind(data, item, start + 1)  # fetch item index
            if tr == -1:  # New key
                data.insert(start + 1, _linemake(item, value, comment))
            else:  # Existing key
                data[tr] = _linemake(item, value, comment)
        del start

        # Reapply formatting
        data = _applyformatting(data)

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
            data = _dataformat(tomlr.read())
    except OSError:
        raise OSError("Toml file not found")
    if data is not None:
        # Find target line
        start = 0
        if subtable is not None:
            start = _tablefind(data, subtable)  # find table offset
        if start != -1:
            tr = _linefind(data, item, start + 1)  # fetch item index
            if tr != -1:
                data.pop(tr)
        del start

        # Reapply formatting
        data = _applyformatting(data)

        # Write to file
        with open(toml, "w") as tomlw:
            for line in data:
                tomlw.write(f"{line}\n")
                del line
    del item, subtable, toml, data
