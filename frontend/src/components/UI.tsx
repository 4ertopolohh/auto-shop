import { useEffect, useState, type ReactNode } from "react";
import { Link } from "react-router-dom";
import { ShoppingBag, RefreshCw } from "lucide-react";
import { money } from "../api";
import { useCart } from "../store";
import type { Product } from "../types";
import s from "./UI.module.scss";
export function Loading({ cards = 4 }: { cards?: number }) {
  return (
    <div
      className={s.skeletonGrid}
      role="status"
      aria-label="Загружаем каталог"
    >
      {Array.from({ length: cards }, (_, i) => (
        <div className={s.skeleton} key={i}>
          <div />
          <span />
          <span />
        </div>
      ))}
    </div>
  );
}
export function ErrorBox({
  message,
  retry,
}: {
  message: string;
  retry?: () => void;
}) {
  return (
    <div className={s.empty}>
      <RefreshCw size={28} />
      <h2>Не получилось загрузить</h2>
      <p>{message}</p>
      {retry && (
        <button className="button" onClick={retry}>
          Попробовать снова
        </button>
      )}
    </div>
  );
}
export function Empty({
  title,
  children,
}: {
  title: string;
  children: ReactNode;
}) {
  return (
    <div className={s.empty}>
      <ShoppingBag size={36} />
      <h2>{title}</h2>
      {children}
    </div>
  );
}
export function Image({
  src,
  alt,
  className = "",
  eager = false,
}: {
  src?: string;
  alt: string;
  className?: string;
  eager?: boolean;
}) {
  const [loaded, setLoaded] = useState(false),
    [failed, setFailed] = useState(false);
  useEffect(() => {
    setLoaded(false);
    setFailed(false);
  }, [src]);
  return (
    <div className={`${s.image} ${!loaded ? s.pending : ""} ${className}`}>
      {src && !failed ? (
        <img
          src={src}
          alt={alt}
          loading={eager ? "eager" : "lazy"}
          decoding="async"
          onLoad={() => setLoaded(true)}
          onError={() => {
            setFailed(true);
            setLoaded(true);
          }}
        />
      ) : (
        <span className={s.fallback}>Фото скоро появится</span>
      )}
    </div>
  );
}
export function ProductCard({ product: p }: { product: Product }) {
  const { add, items } = useCart();
  const inCart = items.some((i) => i.product.id === p.id);
  return (
    <article className={s.card}>
      <Link to={`/product/${p.slug}`} className={s.photo} aria-label={p.name}>
        <Image src={p.images[0]?.url} alt={p.name} />
        {p.badge && <span className={s.badge}>{p.badge}</span>}
      </Link>
      <div className={s.cardInfo}>
        <Link className={s.name} to={`/product/${p.slug}`}>
          {p.name}
        </Link>
        <div className={s.article}>
          <b>{p.brand}</b>
          <span>{p.sku}</span>
        </div>
        <span className={s.stock} data-empty={!p.stock}>
          <i />
          {p.stock ? "В наличии" : "Нет в наличии"}
        </span>
        <div className={s.cardBottom}>
          <div>
            <strong>{money(p.price)}</strong>
            {p.old_price && <del>{money(p.old_price)}</del>}
          </div>
          <button
            className={s.add}
            disabled={!p.stock}
            aria-label={`Добавить ${p.name} в корзину`}
            onClick={() => add(p)}
          >
            {inCart ? "Добавлено" : "В корзину"}
          </button>
        </div>
      </div>
    </article>
  );
}
