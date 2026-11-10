import {
  lazy,
  Suspense,
  useCallback,
  useEffect,
  useRef,
  useState,
} from "react";
import { Link } from "react-router-dom";
import s from "./VehicleExplorer.module.scss";
const CarScene = lazy(() => import("./car/CarScene"));
const parts = [
  {
    id: "engine",
    name: "Двигатель",
    text: "Силовой блок, впуск и система охлаждения. Посмотрите, как всё связано под капотом.",
  },
  {
    id: "brakes",
    name: "Тормозная система",
    text: "Диски и суппорты остаются на своих местах, когда колёса отходят в стороны.",
  },
  {
    id: "suspension",
    name: "Подвеска",
    text: "Колёса, стойки и несущая платформа. Основа уверенного движения.",
  },
  {
    id: "filters",
    name: "Фильтры",
    text: "Воздушный тракт двигателя и пространство салона — найдите свой расходный элемент.",
  },
];
export default function VehicleExplorer() {
  const [active, setActive] = useState("engine"),
    [pinned, setPinned] = useState(false),
    [hovered, setHovered] = useState(false),
    [visible, setVisible] = useState(false);
  const [phase, setPhase] = useState<"loading" | "ready" | "error">("loading");
  const host = useRef<HTMLElement>(null);
  const select = useCallback((category: string) => {
    if (parts.some((p) => p.id === category)) setActive(category);
  }, []);
  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries.some((e) => e.isIntersecting)) {
          setVisible(true);
          observer.disconnect();
        }
      },
      { rootMargin: "220px" },
    );
    if (host.current) observer.observe(host.current);
    return () => observer.disconnect();
  }, []);
  const toggle = useCallback(() => setPinned((value) => !value), []);
  const part = parts.find((p) => p.id === active)!;
  return (
    <section
      className={s.explorer}
      ref={host}
      aria-label="Интерактивный автомобиль"
    >
      <div className={s.copy} data-reveal="left">
        <h2>
          В каждой детали —<br />
          <span>целый автомобиль.</span>
        </h2>
        <p>
          Вращайте автомобиль, чтобы рассмотреть его со всех сторон. Наведите
          курсор на кузов — и он плавно разберётся на слои.
        </p>
        <div className={s.parts} aria-label="Узлы автомобиля">
          {parts.map((p) => (
            <button
              key={p.id}
              aria-pressed={active === p.id}
              onClick={() => setActive(p.id)}
            >
              {p.name}
            </button>
          ))}
        </div>
        <div className={s.partInfo} key={active}>
          <h3>{part.name}</h3>
          <p>{part.text}</p>
          <Link to={`/catalog?category=${part.id}`}>Перейти к деталям</Link>
        </div>
      </div>
      <div className={s.presentation} data-reveal="scale">
        <div
          className={s.stage}
          data-phase={phase}
          data-expanded={pinned || hovered}
        >
          {visible && (
            <Suspense fallback={null}>
              <CarScene
                pinned={pinned}
                onHovered={setHovered}
                onPhase={setPhase}
                onSelect={select}
                onToggle={toggle}
              />
            </Suspense>
          )}
          {phase === "loading" && (
            <div className={s.loading} role="status">
              <div />
              <span>Подготавливаем автомобиль</span>
            </div>
          )}
          {phase === "error" && (
            <div className={s.fallback}>
              <img
                src="/models/sedan-poster.png"
                alt="Чёрный автомобиль без логотипов — вид спереди и сбоку"
                loading="lazy"
              />
              <p>
                В этом браузере 3D недоступно. Откройте сайт в браузере с
                поддержкой WebGL.
              </p>
            </div>
          )}
        </div>
        <p className={s.hint}>
          Перетаскивание — вращение. На телефоне используйте касание автомобиля
          для разборки.
        </p>
      </div>
    </section>
  );
}
