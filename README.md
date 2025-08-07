### 🛠️ GTA SA Path Nodes Editor (Blender 4.0+ Addon)

The **GTA SA Path Nodes Editor** is a powerful Blender addon designed to import, edit, and export `.dat` path node files used by **Grand Theft Auto: San Andreas**. These files control the AI pathfinding for pedestrians and vehicles throughout the game world.

---

### ✨ Features

* ✅ **Full support for `nodes.dat` files**
  Accurately parses and rebuilds all path node data, including:

  * Coordinates (X, Y, Z)
  * Link offsets
  * Area and Node IDs
  * Path width
  * Node type (e.g. car, ped, bike)
  * Flags (bitfield containing behavior and link count)

* 🧠 **Round-trip editing**
  Make changes in Blender’s 3D view or side panel and export a fully valid `nodes.dat` file without losing any data.

* 📌 **In-editor visualization**
  Nodes are represented as 3D empties for easy spatial editing. View and adjust connections between nodes, and inspect link distances.

* 🧩 **Safe export**
  Correctly handles all binary fields — including flag bitfields — to prevent game crashes or AI errors.

* 🧰 **Designed for modders**
  Ideal for map modders, total conversions, or anyone rebuilding path networks for custom GTA SA maps.

---

### 📂 File Format Support

* `.dat` files (GTA SA pathfinding nodes)
