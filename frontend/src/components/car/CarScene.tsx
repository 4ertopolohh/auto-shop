import { useEffect, useRef } from "react";
import * as THREE from "three";
import { GLTFLoader } from "three/addons/loaders/GLTFLoader.js";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
import { RoomEnvironment } from "three/addons/environments/RoomEnvironment.js";
type Props = {
  pinned: boolean;
  onToggle: () => void;
  onHovered: (hovered: boolean) => void;
  onPhase: (phase: "ready" | "error") => void;
  onSelect: (category: string) => void;
};
type MovingLayer = {
  object: THREE.Object3D;
  origin: THREE.Vector3;
  offset: THREE.Vector3;
};
export default function CarScene({
  pinned,
  onToggle,
  onHovered,
  onPhase,
  onSelect,
}: Props) {
  const canvas = useRef<HTMLCanvasElement>(null),
    pin = useRef(pinned),
    wake = useRef<(() => void) | null>(null);
  useEffect(() => {
    pin.current = pinned;
    wake.current?.();
  }, [pinned]);
  useEffect(() => {
    const element = canvas.current;
    if (!element) return;
    const canvasState = element.dataset;
    let renderer: THREE.WebGLRenderer;
    try {
      renderer = new THREE.WebGLRenderer({
        canvas: element,
        antialias: true,
        alpha: true,
        powerPreference: "high-performance",
      });
    } catch {
      onPhase("error");
      return;
    }
    const economical = matchMedia("(pointer:coarse)").matches || (navigator.hardwareConcurrency || 8) <= 4;
    renderer.setPixelRatio(
      Math.min(
        window.devicePixelRatio,
        economical ? 1.15 : 2,
      ),
    );
    renderer.outputColorSpace = THREE.SRGBColorSpace;
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.05;
    renderer.shadowMap.enabled = !economical;
    renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    const scene = new THREE.Scene(),
      camera = new THREE.PerspectiveCamera(33, 1, 0.1, 70),
      home = new THREE.Vector3(5.9, 3.3, 5.6);
    camera.position.copy(home);
    const controls = new OrbitControls(camera, element);
    controls.enableDamping = true;
    controls.dampingFactor = 0.09;
    controls.enablePan = false;
    controls.enableZoom = false;
    controls.minDistance = 4.5;
    controls.maxDistance = 12;
    controls.minPolarAngle = 0.35;
    controls.maxPolarAngle = Math.PI * 0.49;
    controls.rotateSpeed = 0.65;
    controls.zoomSpeed = 0.65;
    controls.target.set(0, 0.7, 0);
    element.style.touchAction = "pan-y";
    const generator = new THREE.PMREMGenerator(renderer),
      room = new RoomEnvironment(),
      environment = generator.fromScene(room, 0.04);
    scene.environment = environment.texture;
    scene.environmentIntensity = 1.2;
    room.dispose();
    generator.dispose();
    scene.add(new THREE.HemisphereLight(0xffffff, 0x7a8170, 1.65));
    const key = new THREE.DirectionalLight(0xffffff, 3.5);
    key.position.set(3, 7, 4);
    key.castShadow = true;
    key.shadow.mapSize.set(economical ? 512 : 2048, economical ? 512 : 2048);
    key.shadow.camera.left = -4;
    key.shadow.camera.right = 4;
    key.shadow.camera.top = 4;
    key.shadow.camera.bottom = -4;
    key.shadow.camera.near = 0.5;
    key.shadow.camera.far = 18;
    key.shadow.normalBias = 0.025;
    key.shadow.bias = -0.0001;
    key.shadow.radius = 4;
    scene.add(key);
    const rim = new THREE.DirectionalLight(0xe5edff, 1.8);
    rim.position.set(-4, 3, -3);
    scene.add(rim);
    const floor = new THREE.Mesh(
      new THREE.PlaneGeometry(60, 60),
      new THREE.ShadowMaterial({ opacity: 0.12 }),
    );
    floor.rotation.x = -Math.PI / 2;
    floor.position.y = -0.012;
    floor.receiveShadow = true;
    scene.add(floor);
    let car: THREE.Group | undefined,
      disposed = false,
      raf = 0,
      last = 0,
      amount = 0,
      hover = false,
      inView = true,
      dragging = false,
      idle = 0;
    const layers: MovingLayer[] = [],
      pointer = new THREE.Vector2(),
      raycaster = new THREE.Raycaster(),
      reduced = matchMedia("(prefers-reduced-motion:reduce)");
    function schedule() {
      if (!disposed && inView && !document.hidden && !raf)
        raf = requestAnimationFrame(frame);
    }
    wake.current = () => {
      idle = 4;
      schedule();
    };
    function frame(now: number) {
      raf = 0;
      if (disposed || !inView || document.hidden) return;
      const dt = last ? Math.min((now - last) / 1000, 0.05) : 1 / 60;
      last = now;
      const target = pin.current || hover ? 1 : 0;
      amount = reduced.matches
        ? target
        : THREE.MathUtils.damp(amount, target, 4.3, dt);
      if (Math.abs(amount - target) < 0.0004) amount = target;
      const eased = amount * amount * (3 - 2 * amount);
      for (const layer of layers)
        layer.object.position
          .copy(layer.origin)
          .addScaledVector(layer.offset, eased);
      controls.target.y = 0.7 + eased * 0.3;
      const moving = controls.update();
      renderer.render(scene, camera);
      canvasState.explosion = amount.toFixed(3);
      if (amount !== target || moving || idle-- > 0) schedule();
    }
    function changed() {
      idle = 2;
      schedule();
    }
    controls.addEventListener("change", changed);
    const resize = () => {
      const rect = element.getBoundingClientRect();
      if (!rect.width || !rect.height) return;
      renderer.setSize(rect.width, rect.height, false);
      camera.aspect = rect.width / rect.height;
      camera.fov = rect.width < 430 ? 46 : 33;
      camera.updateProjectionMatrix();
      changed();
    };
    const resizeObserver = new ResizeObserver(resize);
    resizeObserver.observe(element);
    const observer = new IntersectionObserver((entries) => {
      inView = entries[0].isIntersecting;
      if (inView) {
        last = 0;
        changed();
      } else {
        cancelAnimationFrame(raf);
        raf = 0;
      }
    });
    observer.observe(element);
    const visibility = () => {
      cancelAnimationFrame(raf);
      raf = 0;
      last = 0;
      if (!document.hidden) changed();
    };
    document.addEventListener("visibilitychange", visibility);
    const contextLost = (event: Event) => {
      event.preventDefault();
      onPhase("error");
      cancelAnimationFrame(raf);
      raf = 0;
    };
    element.addEventListener("webglcontextlost", contextLost);
    const hit = (event: PointerEvent) => {
      if (!car) return null;
      const rect = element.getBoundingClientRect();
      pointer.set(
        ((event.clientX - rect.left) / rect.width) * 2 - 1,
        (-(event.clientY - rect.top) / rect.height) * 2 + 1,
      );
      raycaster.setFromCamera(pointer, camera);
      return raycaster.intersectObject(car, true)[0] || null;
    };
    const setHover = (value: boolean) => {
      if (hover !== value) {
        hover = value;
        onHovered(value);
        changed();
      }
    };
    const move = (event: PointerEvent) => {
      if (event.pointerType === "touch" || dragging) return;
      setHover(!!hit(event));
    };
    const leave = () => {
      dragging = false;
      setHover(false);
    };
    let downX = 0,
      downY = 0;
    const down = (event: PointerEvent) => {
      dragging = true;
      downX = event.clientX;
      downY = event.clientY;
    };
    const up = (event: PointerEvent) => {
      dragging = false;
      if (Math.hypot(event.clientX - downX, event.clientY - downY) < 5) {
        if (event.pointerType === "touch" && hit(event)) onToggle();
        let object: THREE.Object3D | undefined = hit(event)?.object;
        while (object) {
          if (object.userData.category) {
            onSelect(String(object.userData.category));
            break;
          }
          object = object.parent || undefined;
        }
      }
      if (event.pointerType !== "touch") setHover(!!hit(event));
    };
    element.addEventListener("pointermove", move);
    element.addEventListener("pointerleave", leave);
    element.addEventListener("pointerdown", down);
    element.addEventListener("pointerup", up);
    element.addEventListener("pointercancel", leave);
    const keyboard = (event: KeyboardEvent) => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        onToggle();
        return;
      }
      if (
        !["ArrowLeft", "ArrowRight", "ArrowUp", "ArrowDown"].includes(event.key)
      )
        return;
      event.preventDefault();
      const orbit = new THREE.Spherical().setFromVector3(
        camera.position.clone().sub(controls.target),
      );
      if (event.key === "ArrowLeft") orbit.theta -= 0.16;
      if (event.key === "ArrowRight") orbit.theta += 0.16;
      if (event.key === "ArrowUp") orbit.phi -= 0.12;
      if (event.key === "ArrowDown") orbit.phi += 0.12;
      orbit.phi = THREE.MathUtils.clamp(
        orbit.phi,
        controls.minPolarAngle,
        controls.maxPolarAngle,
      );
      camera.position
        .copy(controls.target)
        .add(new THREE.Vector3().setFromSpherical(orbit));
      controls.update();
      changed();
    };
    element.addEventListener("keydown", keyboard);
    new GLTFLoader().load(
      "/models/unbranded-sedan.glb",
      (gltf) => {
        if (disposed) {
          disposeModel(gltf.scene);
          return;
        }
        car = gltf.scene;
        car.traverse((object) => {
          if (
            object.name.startsWith("Layer_") &&
            Array.isArray(object.userData.explode)
          ) {
            const [x, y, z] = object.userData.explode as number[];
            layers.push({
              object,
              origin: object.position.clone(),
              offset: new THREE.Vector3(x, z, -y),
            });
          }
          if (object instanceof THREE.Mesh) {
            object.castShadow = true;
            object.receiveShadow = true;
            if (object.material instanceof THREE.MeshStandardMaterial)
              object.material.envMapIntensity = 1.15;
            const materials = Array.isArray(object.material) ? object.material : [object.material];
            for (const material of materials) {
              if (material instanceof THREE.MeshPhysicalMaterial && material.transmission > 0) {
                material.thickness = material.name === "Smoked automotive glass" ? 0.004 : 0.002;
                material.ior = 1.52;
                material.transparent = false;
                material.opacity = 1;
                object.castShadow = false;
              }
            }
          }
        });
        scene.add(car);
        element.dataset.layers = String(layers.length);
        onPhase("ready");
        resize();
        changed();
      },
      undefined,
      () => {
        if (!disposed) onPhase("error");
      },
    );
    resize();
    return () => {
      disposed = true;
      cancelAnimationFrame(raf);
      wake.current = null;
      resizeObserver.disconnect();
      observer.disconnect();
      controls.removeEventListener("change", changed);
      controls.dispose();
      document.removeEventListener("visibilitychange", visibility);
      element.removeEventListener("webglcontextlost", contextLost);
      element.removeEventListener("pointermove", move);
      element.removeEventListener("pointerleave", leave);
      element.removeEventListener("pointerdown", down);
      element.removeEventListener("pointerup", up);
      element.removeEventListener("pointercancel", leave);
      element.removeEventListener("keydown", keyboard);
      if (car) disposeModel(car);
      floor.geometry.dispose();
      (floor.material as THREE.Material).dispose();
      environment.dispose();
      key.shadow.dispose();
      renderer.dispose();
    };
  }, [onHovered, onPhase, onSelect, onToggle]);
  return (
    <canvas
      ref={canvas}
      tabIndex={0}
      role="img"
      aria-label="Объёмная модель чёрного автомобиля без логотипов. Перетаскивайте для вращения, наведите курсор для разборки. Стрелки клавиатуры вращают автомобиль."
    />
  );
}
function disposeModel(root: THREE.Object3D) {
  const geometries = new Set<THREE.BufferGeometry>(),
    materials = new Set<THREE.Material>();
  root.traverse((object) => {
    if (object instanceof THREE.Mesh) {
      geometries.add(object.geometry);
      for (const material of Array.isArray(object.material)
        ? object.material
        : [object.material])
        materials.add(material);
    }
  });
  for (const geometry of geometries) geometry.dispose();
  for (const material of materials) material.dispose();
}
