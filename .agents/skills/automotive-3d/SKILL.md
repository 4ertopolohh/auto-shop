---
name: automotive-3d
description: Rebuild, inspect or export the auto-shop vehicle asset using the project-local Blender Python runtime and official Blender Lab MCP documentation.
---

Use `tools/3d/.venv/Scripts/python.exe` for bpy scripts. The runtime is Blender 5.2.3; do not send geometry to a remote generation service.

The official Blender Lab server is installed locally from https://projects.blender.org/lab/blender_mcp.git (not GitHub), pinned by `tools/3d/setup.ps1`. Its bundled agent prompts and API/manual reference are available in `tools/3d/blender-mcp/mcp/blmcp/data/`. Read only the relevant API pages. Installation and connection details: https://projects.blender.org/lab/blender_mcp/wiki/Setup and https://www.blender.org/lab/mcp-server/.

Use `tools/build_detailed_car.py` to adapt the detailed source. Source files and licences are documented in `assets/3d/SOURCES.md`; keep attribution and the adapted .blend with the exported GLB. GLB uses +Y up; explosion extras remain in Blender coordinates and CarScene converts them.

Before delivery, run mesh QA, inspect assembled and exploded renders from front/side/rear, then import the exported GLB into an empty scene and verify bounds, mesh count, materials and all nonempty Layer_ nodes. Check the actual browser for rotation, hover reassembly, keyboard Enter and touch toggling. Do not describe the adapted compact coupe as an exact Hyundai model.
