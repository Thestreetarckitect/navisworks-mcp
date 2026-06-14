# Navisworks MCP Bridge

Claude MCP integration for Autodesk Navisworks Manage 2027.  
Two-piece architecture: a C# addin running inside Navisworks exposes an HTTP API on `localhost:8765`, and a Python MCP server bridges that API to Claude.

---

## Architecture

```
Claude (MCP client)
      ↕  stdio
Python MCP server (server_http.py)
      ↕  HTTP localhost:8765
C# Addin (MCPBridge.dll) inside Navisworks Manage 2027
      ↕  Navisworks API
.nwd / .nwf model
```

---

## Install

### 1. Deploy the addin (requires admin)

```powershell
# Run as Administrator
.\elevate_deploy.ps1
```

Copies `release\MCPBridge.dll` to:
```
C:\Program Files\Autodesk\Navisworks Manage 2027\Plugins\MCPBridge\
```

> Deploying to `%APPDATA%\Autodesk\...` does **not** load the addin — must be in Program Files.

### 2. Configure Claude MCP

Add to `~/.claude.json` under `mcpServers`:

```json
"navisworks": {
  "command": "C:\\Users\\<user>\\AppData\\Local\\Programs\\Python\\Python312\\python.exe",
  "args": ["C:\\path\\to\\server_http.py"]
}
```

### 3. Open Navisworks

Open Navisworks Manage 2027 → **Add-Ins** ribbon tab → **MCP Bridge** button confirms the listener started.

### 4. Verify

```powershell
Invoke-RestMethod http://localhost:8765/health
```

Expected: `ok v2.1  35 routes`

---

## Requirements

- Autodesk Navisworks Manage **2027** (Freedom not supported)
- Python 3.12+ — full path required in MCP config
- `pip install mcp`

---

## Command Reference

### Quick Reference

| # | Tool | Category | Parameters |
|---|------|----------|-----------|
| 1 | [`health_check`](#health_check) | Health | — |
| 2 | [`get_document_info`](#get_document_info) | Document | — |
| 3 | [`get_model_statistics`](#get_model_statistics) | Document | — |
| 4 | [`list_clash_tests`](#list_clash_tests) | Clash | — |
| 5 | [`create_clash_test`](#create_clash_test) | Clash | `name`, `clash_type`, `tolerance`, `selectionA`, `selectionB` |
| 6 | [`set_clash_selections`](#set_clash_selections) | Clash | `test_name`, `selectionA`, `selectionB` |
| 7 | [`run_clash_test`](#run_clash_test) | Clash | `test_name` *(optional)* |
| 8 | [`get_clash_results`](#get_clash_results) | Clash | `test_name`, `max_results` |
| 9 | [`delete_clash_test`](#delete_clash_test) | Clash | `test_name` |
| 10 | [`create_clash_group`](#create_clash_group) | Clash Groups | `test_name`, `group_name` |
| 11 | [`list_clash_groups`](#list_clash_groups) | Clash Groups | `test_name` |
| 12 | [`delete_clash_group`](#delete_clash_group) | Clash Groups | `test_name`, `group_name` |
| 13 | [`add_clashes_to_group`](#add_clashes_to_group) | Clash Groups | `test_name`, `group_name`, `clash_names[]` |
| 14 | [`set_clash_group_status`](#set_clash_group_status) | Clash Groups | `test_name`, `group_name`, `status` |
| 15 | [`list_sets`](#list_sets) | Sets | — |
| 16 | [`create_selection_set`](#create_selection_set) | Sets | `name` |
| 17 | [`get_selection_set_items`](#get_selection_set_items) | Sets | `name` |
| 18 | [`create_search_set`](#create_search_set) | Sets | `name`, `category`, `property`, `operator`, `value` |
| 19 | [`execute_search_set`](#execute_search_set) | Sets | `name` |
| 20 | [`delete_set`](#delete_set) | Sets | `name` |
| 21 | [`find_items`](#find_items) | Find | `value`, `category`, `property`, `operator`, `limit`, `select_results` |
| 22 | [`find_items_by_name`](#find_items_by_name) | Find | `pattern`, `limit`, `select_results` |
| 23 | [`select_all`](#select_all) | Selection | — |
| 24 | [`deselect_all`](#deselect_all) | Selection | — |
| 25 | [`invert_selection`](#invert_selection) | Selection | — |
| 26 | [`select_from_set`](#select_from_set) | Selection | `name` |
| 27 | [`get_current_selection`](#get_current_selection) | Selection | — |
| 28 | [`get_element_properties`](#get_element_properties) | Selection | `name` *(optional)* |
| 29 | [`color_elements`](#color_elements) | Visuals | `r`, `g`, `b` |
| 30 | [`set_transparency`](#set_transparency) | Visuals | `transparency` |
| 31 | [`hide_elements`](#hide_elements) | Visuals | — |
| 32 | [`unhide_all`](#unhide_all) | Visuals | — |
| 33 | [`isolate_elements`](#isolate_elements) | Visuals | — |
| 34 | [`reset_overrides`](#reset_overrides) | Visuals | — |
| 35 | [`list_viewpoints`](#list_viewpoints) | Viewpoints | — |
| 36 | [`save_viewpoint`](#save_viewpoint) | Viewpoints | `name` |
| 37 | [`goto_viewpoint`](#goto_viewpoint) | Viewpoints | `name` |
| 38 | [`delete_viewpoint`](#delete_viewpoint) | Viewpoints | `name` |
| 39 | [`get_current_viewpoint`](#get_current_viewpoint) | Viewpoints | — |

---

### Health & Document

#### `health_check`
Verify the Navisworks addin is running and reachable on localhost:8765.  
No parameters.

#### `get_document_info`
Return metadata for the currently open Navisworks document (filename, title, units, model count).  
No parameters.

#### `get_model_statistics`
Element counts grouped by class (walls, pipes, ducts, structural members, etc.).  
No parameters.

---

### Clash Detection

#### `list_clash_tests`
List all clash tests in the current document with their status and result counts.  
No parameters.

#### `create_clash_test`

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `name` | string | **required** | Name for the new clash test |
| `clash_type` | `Hard` \| `Clearance` \| `Duplicate` | `Hard` | Clash type |
| `tolerance` | number | `0.001` | Clearance tolerance in model units |
| `selectionA` | string | — | Selection-set or search-set to assign to side A |
| `selectionB` | string | — | Selection-set or search-set to assign to side B |

#### `set_clash_selections`
Attach selection-sets or search-sets to an existing clash test.

| Parameter | Type | Description |
|-----------|------|-------------|
| `test_name` | string | **required** — name of the clash test |
| `selectionA` | string | Set name for side A |
| `selectionB` | string | Set name for side B |

#### `run_clash_test`
Run a clash test by name, or all tests if name omitted.

| Parameter | Type | Description |
|-----------|------|-------------|
| `test_name` | string | Clash test name (omit to run all) |

#### `get_clash_results`
Return clash results for a named test.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `test_name` | string | **required** | Clash test name |
| `max_results` | integer | `100` | Maximum results to return |

#### `delete_clash_test`
Delete a clash test by name.

| Parameter | Type | Description |
|-----------|------|-------------|
| `test_name` | string | **required** |

---

### Clash Groups

#### `create_clash_group`
Create an empty clash group inside an existing clash test.

| Parameter | Type | Description |
|-----------|------|-------------|
| `test_name` | string | **required** |
| `group_name` | string | **required** |

#### `list_clash_groups`
List clash groups inside a clash test, with their child clash result names.

| Parameter | Type | Description |
|-----------|------|-------------|
| `test_name` | string | **required** |

#### `delete_clash_group`
Delete a clash group and its child results from a clash test.

| Parameter | Type | Description |
|-----------|------|-------------|
| `test_name` | string | **required** |
| `group_name` | string | **required** |

#### `add_clashes_to_group`
Move ungrouped clash results into a clash group. Pass display names (e.g. `Clash1`, `Clash2`).

| Parameter | Type | Description |
|-----------|------|-------------|
| `test_name` | string | **required** |
| `group_name` | string | **required** |
| `clash_names` | string[] | **required** — display names of clashes to move |

#### `set_clash_group_status`
Set the review status of a clash group.

| Parameter | Type | Values |
|-----------|------|--------|
| `test_name` | string | **required** |
| `group_name` | string | **required** |
| `status` | string | `New` \| `Active` \| `Reviewed` \| `Approved` \| `Resolved` |

---

### Selection & Search Sets

#### `list_sets`
List all selection sets and search sets in the document.  
No parameters.

#### `create_selection_set`
Create a selection set from the **current viewport selection**.

| Parameter | Type | Description |
|-----------|------|-------------|
| `name` | string | **required** |

#### `get_selection_set_items`
List the elements stored in a named selection set.

| Parameter | Type | Description |
|-----------|------|-------------|
| `name` | string | **required** |

#### `create_search_set`
Create a saved search with a single property condition.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `name` | string | **required** | Name for the search set |
| `category` | string | `Item` | Property category (e.g. `Item`, `Element`, `LcRevit`) |
| `property` | string | `Name` | Property name within the category |
| `operator` | string | `contains` | `equals` \| `contains` \| `startsWith` \| `endsWith` |
| `value` | string | **required** | Search value |

#### `execute_search_set`
Run a saved search and return the count of matching elements.

| Parameter | Type | Description |
|-----------|------|-------------|
| `name` | string | **required** |

#### `delete_set`
Delete a selection set or search set by name.

| Parameter | Type | Description |
|-----------|------|-------------|
| `name` | string | **required** |

---

### Find & Select

#### `find_items`
Single-condition property search returning matching elements.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `value` | string | **required** | Value to search for |
| `category` | string | `Item` | Property category |
| `property` | string | `Name` | Property name |
| `operator` | string | `contains` | `equals` \| `contains` \| `startsWith` \| `endsWith` |
| `limit` | integer | `50` | Max results to return |
| `select_results` | boolean | `false` | Select matches in viewport |

#### `find_items_by_name`
Quick substring search by element name.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `pattern` | string | **required** | Substring to search |
| `limit` | integer | `50` | Max results |
| `select_results` | boolean | `true` | Select matches in viewport |

#### `select_all`
Select every element in the model.  
No parameters.

#### `deselect_all`
Clear the current selection.  
No parameters.

#### `invert_selection`
Invert the current selection (select unselected, deselect selected).  
No parameters.

#### `select_from_set`
Replace the current selection with the contents of a named set.

| Parameter | Type | Description |
|-----------|------|-------------|
| `name` | string | **required** |

#### `get_current_selection`
Return the elements currently selected in the viewport.  
No parameters.

#### `get_element_properties`
Return all property tabs and values for the first selected element, or search by name.

| Parameter | Type | Description |
|-----------|------|-------------|
| `name` | string | Element name to look up (optional — uses current selection if omitted) |

---

### Color & Visibility

#### `color_elements`
Override the color of the **currently selected** elements.

| Parameter | Type | Description |
|-----------|------|-------------|
| `r` | integer 0–255 | Red |
| `g` | integer 0–255 | Green |
| `b` | integer 0–255 | Blue |

**Example — brand green `#02E482`:**
```
r: 2   g: 228   b: 130
```

#### `set_transparency`
Override transparency of the currently selected elements.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `transparency` | number 0.0–1.0 | `0.5` | `0.0` = fully opaque, `1.0` = fully transparent |

#### `hide_elements`
Hide the currently selected elements.  
No parameters.

#### `unhide_all`
Restore visibility of every hidden element.  
No parameters.

#### `isolate_elements`
Hide everything **except** the current selection.  
No parameters.

#### `reset_overrides`
Remove every color and transparency override and unhide everything.  
No parameters.

---

### Viewpoints

#### `list_viewpoints`
List all saved viewpoints.  
No parameters.

#### `save_viewpoint`
Save the current camera position as a named viewpoint.

| Parameter | Type | Description |
|-----------|------|-------------|
| `name` | string | **required** |

#### `goto_viewpoint`
Navigate to a saved viewpoint by name.

| Parameter | Type | Description |
|-----------|------|-------------|
| `name` | string | **required** |

#### `delete_viewpoint`
Delete a saved viewpoint by name.

| Parameter | Type | Description |
|-----------|------|-------------|
| `name` | string | **required** |

#### `get_current_viewpoint`
Return the current camera position, direction, and projection type.  
No parameters.

---

## Example Workflows

### Run a hard-clash check between structure and MEP
```
1. create_search_set  name="Structure"  category="LcRevit"  property="Category"  operator="contains"  value="Structural"
2. create_search_set  name="MEP"        category="LcRevit"  property="Category"  operator="contains"  value="Mechanical"
3. create_clash_test  name="STR vs MEP"  clash_type="Hard"  selectionA="Structure"  selectionB="MEP"
4. run_clash_test     test_name="STR vs MEP"
5. get_clash_results  test_name="STR vs MEP"  max_results=200
```

### Group and triage clashes
```
1. create_clash_group  test_name="STR vs MEP"  group_name="Level 3 - Critical"
2. add_clashes_to_group  test_name="STR vs MEP"  group_name="Level 3 - Critical"  clash_names=["Clash1","Clash2","Clash5"]
3. set_clash_group_status  test_name="STR vs MEP"  group_name="Level 3 - Critical"  status="Active"
```

### Color model by trade
```
1. find_items_by_name  pattern="HVAC"  select_results=true
2. color_elements  r=255  g=165  b=0        # orange for MEP
3. find_items_by_name  pattern="COL-"  select_results=true
4. color_elements  r=128  g=128  b=128      # grey for columns
```

### Save camera positions for a review
```
1. goto_viewpoint  name="Entry Lobby"
2. save_viewpoint  name="Clash Review - Grid A"
3. save_viewpoint  name="Clash Review - Roof"
4. list_viewpoints
```

---

## Files

| File | Purpose |
|------|---------|
| `server_http.py` | Python MCP server — bridges Claude to Navisworks HTTP API |
| `MCPBridgePlugin.cs` | C# Navisworks addin source |
| `ClashGroupHandlers.cs` | Clash group handler source |
| `NavisworksMcpAddin.csproj` | VS project (targets net48, Navisworks API v24) |
| `release/MCPBridge.dll` | Prebuilt addin DLL — deploy this |
| `release/MCPBridge.pdb` | Debug symbols |
| `elevate_deploy.ps1` | Deploy script (copies DLL to Program Files, requires admin) |
| `make_clash_report.py` | Utility: generate clash report from Navisworks via MCP |

---

## Known Gotchas

- `.addin` manifest is Revit format — Navisworks ignores it. Remove it.
- `Install-Addin.ps1` from upstream has a parse error — use `elevate_deploy.ps1` instead.
- Navisworks 2020 / 2022 also installed but **not** supported (API version mismatch).
- Python scripts dir is not on PATH — use full `python.exe` path in MCP config.
- Addin log: `%TEMP%\navisworks_mcp_addin.log`
