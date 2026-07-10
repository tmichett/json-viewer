# JSON Viewer — User Guide

JSON Viewer is a desktop application that lets you edit structured data (JSON, YAML, or XML) in a syntax-highlighted editor and explore it as an interactive node graph — similar to [JSON Crack](https://jsoncrack.com), but as a native app on your machine.

## Getting started

### Run from source

```bash
cd json-viewer
uv sync --group dev
uv run json-viewer
```

### Run the compiled app (macOS)

After building with `./scripts/build.sh`:

```bash
open "dist/JSON Viewer.app"
```

On first launch, macOS may prompt you to allow the unsigned app (right-click → Open).

---

## Interface overview

The window has three main areas:

```
┌─ Menu bar: File | View | Tools | Help ──────────────────────┐
├─ Editor (left) ─────────┬─ Graph canvas (right) ────────────┤
│  Line numbers           │  Interactive node graph           │
│  Syntax highlighting    │  Zoom slider (bottom-right)       │
├─ Search bar ────────────┴─ Zoom toolbar (− + Fit Root) ─────┤
└─ Status: Valid | error detail | Live Transform | View as ───┘
```

### Left pane — Editor

- Syntax-highlighted text editor with line numbers
- **Keys** appear in bold purple/blue
- **Braces and brackets** `{ } [ ]` appear in bold orange
- **Strings, numbers, booleans, and null** each have distinct colors
- Place the cursor on a brace to highlight its matching pair

### Right pane — Graph

- Hierarchical node-link diagram of your data
- Drag to pan; scroll to move vertically
- **Ctrl+scroll** (or the zoom slider) to zoom in/out
- Click **− / +** on the left of `{N keys}` or `[N items]` rows to collapse/expand that section
- Click the blue **+** on the right of an array row to add a new item
- Click **+ Add key** at the bottom of object nodes to add a property
- Click any scalar value (string, number, etc.) to edit it in a dialog
- Hex color values (e.g. `#FF0000`) show a small color swatch
- Faint horizontal lines separate rows inside each node (JSON Crack style)
- Graph edits sync back to the text editor automatically

### Bottom controls

| Control | Purpose |
|---------|---------|
| **Preview** | Switch right pane between **Graph** and **Table** views |
| **Search nodes** | Find graph nodes by key or value; use ◀ ▶ to cycle matches (graph mode) |
| **− + Fit Root** | Zoom out, zoom in, fit graph to view, focus root node |
| **Zoom slider** | Drag the slider in the graph pane (bottom-right) for fine zoom control |
| **Valid / Invalid** | Live syntax status; click **Invalid** to jump to the error |
| **Live Transform** | When On, the graph updates as you type (300 ms debounce) |
| **View as** | Switch editor format between JSON, YAML, and XML |

---

## Working with files

### Open a file

- **File → Open** (Cmd/Ctrl+O)
- Drag and drop a `.json`, `.yaml`, `.yml`, or `.xml` file onto the window

The format is detected from the file extension and the **View as** dropdown updates automatically.

### Save a file

- **File → Save** (Cmd/Ctrl+S)
- **File → Save As** (Cmd/Ctrl+Shift+S)

Files are saved in the currently selected **View as** format.

### Format / beautify

**Tools → Format Document** (Cmd/Ctrl+Shift+F) re-indents and normalizes the current document without changing the data.

---

## Format switching (View as)

The **View as** dropdown in the status bar converts the editor content between formats while keeping the graph in sync.

**Example workflow:**

1. Start with JSON in the editor
2. Change **View as** to `YAML` — the text converts to YAML with YAML highlighting
3. The graph on the right is unchanged (same data, different representation)
4. Switch back to `JSON` at any time

> [!tip] XML conversion
> XML uses a structured element format. Arrays appear as repeated `<item>` children. If conversion fails, the linter will show the error location — fix the source format first, then retry.

Supported round-trips: JSON ↔ YAML ↔ XML (when the data structure is compatible).

---

## Live linter

The editor validates syntax continuously as you type.

**When valid:** status bar shows green **Valid**.

**When invalid:**

- Status bar shows **Invalid — click to jump** with an error message (line and column)
- The error line is **bold red** in the gutter
- A red tinted background and wavy underline mark the error in the editor

**Navigation:**

| Action | Shortcut |
|--------|----------|
| Jump to first error | **F8** or click **Invalid** in status bar |
| List all errors | **Tools → Validate Document** (Cmd/Ctrl+Shift+V) |

The linter runs even when **Live Transform** is off, so you always get syntax feedback while editing.

---

## Table preview

Switch the right pane from the relationship graph to a **spreadsheet-style table** — useful for array data like database records.

### Enable table view

- Choose **Table** from the **Preview** dropdown in the status bar, or
- **View → Table Preview** (Ctrl+Shift+T on Windows/Linux, Cmd+Shift+T on macOS)

Return to the graph with **View → Graph Preview** (Ctrl+Shift+G).

### Choose which array

Use the **Table** dropdown at the top of the table pane to pick an array (e.g. `fruits`). The app discovers all arrays in the document, including nested ones like `data.items`.

### Columns and rows

The table view organizes data like a **relational database**, not one wide flat spreadsheet:

- **Main table** (e.g. `fruits`) — primary key column first (`name`), then other top-level fields (`color`)
- **Related tables** (e.g. `details`, `nutrients`) — one per nested object, linked back via the primary key (`name →`)
- Foreign key columns in child tables are read-only; edit the main table to change the key
- Scalar arrays (e.g. `["a", "b"]`) still show a single **value** column
- **Field order** — form fields and table columns follow the key order in your JSON document (e.g. `name`, `color`, then `details`, `nutrients`), not alphabetical order
- **Compact layout** — each table sizes to its rows; sections stack at the top without large empty gaps

### Edit cells

Double-click any cell to edit. Changes sync to the text editor immediately and mark the document as unsaved.

### Add a dataset

Click **+ Dataset** in the table header (or on the empty state) to create a new top-level array — e.g. `vegetables` alongside `fruits`. Enter a name; an empty array is added to the JSON root. Switch to it in the **Dataset** dropdown, then use **+ Add row** to populate it.

### Add rows to a dataset

On the **main table** (e.g. `fruits`), click **+ Add row** below the grid. This opens the same schema-based form as graph **+** on an array — fill in `name`, `color`, `details`, `nutrients`, etc. for a new item like Grapes.

Child tables (`details`, `nutrients`) do not have their own add-row button — rows are tied to the main table. Add a row on `fruits`, then fill in child table cells.

Use **+ Add key** below a child table to add a new field to that nested object on every row (e.g. add `origin` to all `details` records). Double-click cells to set values per item.

---

## Graph interaction

### Zoom and pan

| Method | Action |
|--------|--------|
| Drag (hand cursor) | Pan the graph |
| Scroll wheel | Pan vertically |
| Ctrl + scroll | Zoom in/out |
| Zoom slider (graph pane) | Fine-grained zoom (10%–400%) |
| **− / +** buttons | Step zoom by 15% |
| **Fit** | Fit entire graph to the viewport |
| **Root** | Center on the root node |

### Collapse and expand

- Click **−** on the left of `{N keys}` or `[N items]` on a node to collapse that section
- Click **+** on the left to expand it again
- **Tools → Collapse All** / **Expand All** for bulk operations

Collapsed sections hide child nodes from the graph, which helps with large documents.

> [!note] Two kinds of **+**
> The **+ / −** on the *left* of a row collapses or expands children. The blue **+** on the *right* of an array row adds a new item. **+ Add key** at the bottom of a node adds a property.

### Editing data on the graph

You can add and change data directly on the graph without editing raw JSON. Changes appear in the text editor immediately and mark the document as unsaved.

#### Add an item to an array

1. Find the array row (e.g. `fruits: [3 items]`) on a node
2. Click the blue **+** on the right side of that row
3. A form opens with fields inferred from existing items in the array

For object arrays (like the sample `fruits` data), the form shows all top-level keys and nested groups (`details`, `nutrients`, etc.) in **JSON key order** — e.g. `name`, `color`, then nested groups. Keys are merged across siblings — if one fruit has `vitaminC` and another has `potassium`, both appear in the form.

4. Fill in the fields and click **OK** — the new item is added with full structure

For string or number arrays, a simple single-value dialog appears instead.

> [!tip] Empty arrays
> If the array has no existing items to copy structure from, a blank `{}` is added. Use **+ Add key** on the new node to build it up field by field.

#### Add a key to an object

1. Open any object node (e.g. a fruit entry or the root document)
2. Click **+ Add key** at the bottom of the node
3. Enter the key name, type, and value in the dialog
4. Click **OK**

#### Edit an existing value

1. Click any scalar row on a node (e.g. `name: Apple` or `calories: 52`)
2. Edit the value in the dialog that opens
3. Click **OK**

#### Example workflow — add a new fruit

1. Click **+** on the `fruits: [N items]` row in the root node
2. In the **Add Fruit** dialog, fill in:
   - `name`: Grapes
   - `color`: `#800080`
   - `details` → `type`: Berry, `season`: Summer
   - `nutrients` → `calories`: 69, `fiber`: 0.9g, etc.
3. Click **OK** — the graph shows the new node and the JSON editor updates

To add a single extra field later (e.g. `price` on one fruit), use **+ Add key** on that fruit's node instead.

### Search nodes

1. Type in the **Search nodes** field at the bottom of the graph pane
2. Matching nodes are highlighted; the view centers on the current match
3. Use ◀ ▶ buttons to cycle through matches

### Node limit

Graphs with more than **1500 nodes** show an overlay instead of rendering. To work around this:

- Collapse large sections
- Reduce the data size
- Focus on a subtree by editing the source

---

## Help menu

| Item | Description |
|------|-------------|
| **Help → Usage...** (F1) | Scrollable in-app guide — editor, graph editing, navigation, shortcuts |
| **Help → About JSON Viewer** | Application name, version number, JSON Crack credit, license |

The version shown in About matches `json_viewer.__version__` (currently **0.1.0**).

---

## Themes

**View → Toggle Theme** (Cmd/Ctrl+T) switches between light and dark mode.

Your preference is saved and restored on next launch.

---

## Export

**File → Export PNG** or **File → Export SVG** saves the current graph visualization as an image.

The export captures what is visible in the graph canvas at the time of export.

---

## Keyboard shortcuts

| Action | macOS | Windows/Linux |
|--------|-------|---------------|
| Open file | Cmd+O | Ctrl+O |
| Save | Cmd+S | Ctrl+S |
| Save As | Cmd+Shift+S | Ctrl+Shift+S |
| Format document | Cmd+Shift+F | Ctrl+Shift+F |
| Validate document | Cmd+Shift+V | Ctrl+Shift+V |
| Toggle theme | Cmd+T | Ctrl+T |
| Toggle live transform | Cmd+L | Ctrl+L |
| Fit graph | Cmd+0 | Ctrl+0 |
| Search nodes | Cmd+F | Ctrl+F |
| Graph preview | Cmd+Shift+G | Ctrl+Shift+G |
| Table preview | Cmd+Shift+T | Ctrl+Shift+T |
| Go to error | F8 | F8 |
| Usage help | F1 | F1 |
| Quit | Cmd+Q | Ctrl+Q |

---

## Troubleshooting

### Graph does not update

- Check that **Live Transform** is **On** in the status bar
- If the status shows **Invalid**, fix the syntax error first (press F8 to jump to it)
- Toggle Live Transform off and on to force a refresh

### Graph edit did not appear in the editor

- Graph edits require valid JSON/YAML/XML — fix any syntax errors first
- The document is marked unsaved (`*` in the title bar) after graph edits; save with **File → Save**

### Add-item form is empty or only adds `{}`

- The form infers fields from **existing non-empty items** in the array
- If the array is empty or only contains blank `{}` entries, use **+ Add key** on the new node to add fields manually

### View as conversion failed

- The source document must be valid in its current format before converting
- XML conversion requires data that maps cleanly to an XML tree (objects and arrays)
- Use **Tools → Validate Document** to see the specific error

### Graph shows "exceeds node limit"

- Your document has more than 1500 graph nodes
- Collapse nested sections using **Tools → Collapse All**, then expand only what you need
- Consider working with a smaller subset of the data

### macOS app won't open

- Right-click the app → **Open** (for unsigned builds)
- Or run from source: `uv run json-viewer`

### Zoom slider and buttons out of sync

- Click **Fit** to reset the view; the slider updates to match

---

## Example data

On first launch, the editor loads a sample `fruits` JSON document demonstrating nested objects, arrays, and hex color values. Use it to explore the graph, try format switching, test collapse/search, and practice adding or editing items on the graph.

---

## Privacy

All parsing and rendering happens locally on your machine. No data is sent to any server.
