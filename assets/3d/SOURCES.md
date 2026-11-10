# Vehicle source and tools

The current detailed compact coupe is adapted from Mike Pan's BMW 1 Series M Blender demonstration, downloaded from the official Blender distribution archive:
https://download.blender.org/demo/test/BMW27_2.blend.zip
Original author profile/model listing: https://blendswap.com/3d/bmw (Mike Pan, CC BY-SA).
We distribute the adapted .blend and GLB under CC BY-SA 3.0: https://creativecommons.org/licenses/by-sa/3.0/ . Attribution: Mike Pan, adaptation for Triad Studio auto-shop demo. The model is not an exact Hyundai Solaris/Elantra replica. Manufacturer emblems and licence plates have been removed. Wheel hubs carry no badges.

Changes: black PBR paint, rebuilt materials, separated assemblies and hood, neutral branding, straight wheels, added mechanical internals, cleaned/triangulated web geometry. `tools/build_car.py` preserves the previous original procedural source and generates the internal parts; `tools/build_detailed_car.py` creates the detailed delivery.

Agent tooling is installed in tools/3d/.venv: bpy 5.2.3 and official Blender Lab MCP 1.0.2. MCP source comes from Blender's own Forgejo at https://projects.blender.org/lab/blender_mcp.git, revision dbbf836ad4b1025f14a2b3b504c43903f39e0b04. No GitHub source is used. The model was processed with the local bpy runtime; interactive MCP attachment is optional and is not claimed as active.

Rebuild: run tools/build_car.py first to create the internal assemblies, copy its blend to backend/.local/car-source/procedural-internals.blend, unpack the official BMW zip into backend/.local/car-source/bmw27, then run tools/build_detailed_car.py. Generated QA details live in backend/.local/car-review. See the model-report.json for delivered mesh statistics.

## November 2026 detail pass

Run `tools/3d/.venv/Scripts/python.exe tools/enhance_car.py` directly on the delivered `.blend`; original download intermediates are not required. This idempotent pass preserves the source mesh and 16 assembly extras, adds cabin upholstery/control details, cooling, powertrain, suspension, calipers, wipers and mirror inserts. It adjusts clearcoat paint and transmission glazing. Optical shells intentionally remain thin surfaces to avoid coincident body/frame faces; browser rendering supplies a 4 mm optical thickness with IOR 1.52.

QA accepts duplicate positions at separate capped tube islands (welding touching shells creates non-manifold junctions) and the existing hidden back-to-back source faces. These do not change the outer silhouette or assembly controls. Licensing and attribution above continue to apply to the adapted geometry.
