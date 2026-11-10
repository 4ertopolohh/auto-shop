# Visual upgrade verification

- Source: adapted existing CC BY-SA coupe; attribution retained in assets/3d/SOURCES.md. Rebuild detail pass with tools/3d/.venv/Scripts/python.exe tools/enhance_car.py.
- Delivered GLB: 56 meshes/primitives, 16 materials, 359410 triangles, 8418592 bytes; 16 nonempty Layer_ nodes, original bounds and explode/category extras retained. Clearcoat, transmission and IOR extensions verified in GLB JSON.
- Mesh QA: no errors. Accepted warnings are separate capped tube islands with coincident end positions and existing hidden source faces; welding all coincident vertices introduces non-manifold junctions.
- Assembled/exploded front, side and rear review sheets inspected; poster rendered with Cycles. Review sheets and full QA: backend/.local/car-review. Roundtrip report: assets/3d/roundtrip-report.json.
- Browser: paint reflections, visible cabin, 16 layers, drag rotation, Enter/arrow control, reassembly to data-explosion=0.000 after pointer moved to blank canvas. No browser console errors in final session.
- Storefront: home, catalog, product gallery, add to cart, quantity and checkout delivery pricing checked. Mobile 390px layout and menu checked. Real touch hardware and browser reduced-motion emulation were unavailable; these paths were inspected in code.
- npm run build passed (Vite warns about the lazily loaded Three.js chunk size). Final npm run typecheck and git diff --check passed. Favicon verified byte-for-byte in Vite output.
- Motion uses IntersectionObserver/MutationObserver and scroll-coalesced requestAnimationFrame without new dependencies. Reduced motion bypasses reveals and parallax; keyboard focus reveals its containing content immediately.
