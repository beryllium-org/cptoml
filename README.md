# CPToml

A CircuitPython module for managing toml files.<br />
<br />
To create an .mpy package, just run <code>make mpy</code>.<br />
<br />
Basic usage guide:<br />
```
# Read
from cptoml import fetch
fetch("CIRCUITPY_PYSTACK_SIZE") # To fetch something from the root table
fetch("item1", "subtable1") # To fetch item1 from subtable1

# Write
from cptoml import put
from storage import remount
remount("/", False)
put("CIRCUITPY_PYSTACK_SIZE", 7000) # To set an item in root table
put("item1", 123, "subtable1", comment="This is useless") # To set item1 in subtable1 with comment
remount("/", True)

# Delete
from cptoml import delete
from storage import remount
remount("/", False)
delete("CIRCUITPY_PYSTACK_SIZE") # To make me sad
delete("item1", "subtable1") # To delete item1 from subtable1
remount("/", True)
```
<br />
Empty tables are deleted automatically.<br />
The toml file is formatted automatically on any write.<br />
To edit a toml file other than <code>/settings.toml</code>, pass the option: <code>toml="/path_to_your.toml"</code>.<br />
