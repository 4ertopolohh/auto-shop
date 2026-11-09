# Vehicle source and tools

The current detailed compact coupe is adapted from Mike Pan's BMW 1 Series M Blender demonstration, downloaded from the official Blender distribution archive:
https://download.blender.org/demo/test/BMW27_2.blend.zip
Original author profile/model listing: https://blendswap.com/3d/bmw (Mike Pan, CC BY-SA).
We distribute the adapted .blend and GLB under CC BY-SA 3.0: https://creativecommons.org/licenses/by-sa/3.0/ . Attribution: Mike Pan, adaptation for Triad Studio auto-shop demo. The model is not an exact Hyundai Solaris/Elantra replica. Manufacturer emblems and licence plates have been removed. Wheel hubs carry no badges.

Changes: black PBR paint, rebuilt materials, separated assemblies and hood, neutral branding, straight wheels, added mechanical internals, cleaned/triangulated web geometry. `tools/build_car.py` preserves the previous original procedural source and generates the internal parts; `tools/build_detailed_car.py` creates the detailed delivery.

Agent tooling is installed in tools/3d/.venv: bpy 5.2.3 and official Blender Lab MCP 1.0.2. MCP source comes from Blender's own Forgejo at https://projects.blender.org/lab/blender_mcp.git, revision dbbf836ad4b1025f14a2b3b504c43903f39e0b04. No GitHub source is used. The model was processed with the local bpy runtime; interactive MCP attachment is optional and is not claimed as active.

Rebuild: run tools/build_car.py first to create the internal assemblies, copy its blend to backend/.local/car-source/procedural-internals.blend, unpack the official BMW zip into backend/.local/car-source/bmw27, then run tools/build_detailed_car.py. Generated QA details live in backend/.local/car-review. See the model-report.json for delivered mesh statistics.
