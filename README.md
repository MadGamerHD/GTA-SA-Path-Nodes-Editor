# GTA SA Path Nodes Editor

A Blender 4.0 add‑on for importing, editing, and exporting Grand Theft Auto: San Andreas `nodes.dat` path files.

---

## Features

* **Multi‑file import**: Load one or more `nodesXX.dat` files at once, automatically grouped into a `PathNodes` collection.
* **Full data round‑trip**: Reads all node coordinates and link pairs; stores them in Blender’s scene properties for editing.
* **In‑UI editing**: Browse and modify node positions (X, Y, Z) and link relationships directly in the 3D View sidebar (N‑panel).
* **Add & link nodes**: Create new nodes on the fly, select any two path nodes in the viewport and link them with automatic distance calculation.
* **Export back to DAT**: Saves all current nodes and link pairs into a valid `nodes.dat` file.
---

## Usage

1. **Import**

   * Open the 3D Viewport and press **N** to reveal the sidebar.
   * Switch to the **Path Nodes** tab.
   * Click **Import .dat Files**, select one or multiple `nodes*.dat` files, and click **Import**.
   * A new `PathNodes` collection will appear, with empties representing each node.

2. **Edit**

   * In the sidebar list, select a node to view/edit its X, Y, Z coordinates and link count.
   * Move nodes in the viewport as needed—coordinates will update on export.
   * To link two nodes: select them in the viewport, then click **Link Selected Nodes** (or your link operator). The new link appears in the list.
   * To add a new node: click **Add Node** and adjust its coordinates.

3. **Export**

   * Click **Export .dat**.
   * Choose a file name (e.g. `nodes_out.dat`) and save.
   * The exported file will contain updated node positions and link pairs.

---

## How It Works

* **Data Storage**: Each path node is stored in a `Scene.pathnodes` collection, with properties for coordinates, link indices, and more.
* **Empties**: Each node spawns an Empty object in a `PathNodes` Blender collection, tagged via a custom property (`is_pathnode`) for easy clearing.
* **Import/Export**: Uses Python’s `struct` module to read/write the GTA SA binary `.dat` format (`<IIIII` header, followed by node records and link pairs).

---

## Preview
![Screenshot 2025-05-07 234846](https://github.com/user-attachments/assets/21a57da5-dd78-4f83-8d1a-0d57398bb620)

*Sidebar UI showing imported nodes, editable coordinates, and link list.*
