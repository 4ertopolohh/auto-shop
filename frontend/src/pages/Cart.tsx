import { Link } from "react-router-dom";
import { Truck } from "lucide-react";
import { useCart } from "../store";
import { money } from "../api";
import { Empty, Image } from "../components/UI";
import s from "./Commerce.module.scss";
export default function Cart() {
  const { items, count, total, change } = useCart();
  return (
    <div className="container">
      <div className="breadcrumb">
        <Link to="/">Главная</Link>
        <span>Корзина</span>
      </div>
      <h1 className="pageTitle">
        Ваши детали<span className={s.count}>{count}</span>
      </h1>
      <p className={s.subtitle}>Всё нужное для следующего километра.</p>
      {!items.length ? (
        <Empty title="Здесь пока тихо">
          <p>Найдите нужные запчасти — мы соберём их здесь.</p>
          <Link className="button" to="/catalog">
            Перейти в каталог
          </Link>
        </Empty>
      ) : (
        <div className={s.layout}>
          <div className={s.cartItems}>
            {items.map(({ product: p, quantity }) => (
              <article className={s.cartItem} key={p.id}>
                <Link to={`/product/${p.slug}`} className={s.cartImage}>
                  <Image src={p.images[0]?.url} alt={p.name} />
                </Link>
                <div className={s.itemInfo}>
                  <span>
                    {p.brand} / {p.sku}
                  </span>
                  <Link to={`/product/${p.slug}`}>{p.name}</Link>
                  <p>В наличии · {money(p.price)} за шт.</p>
                </div>
                <div className={s.quantity}>
                  <button
                    onClick={() => change(p.id, quantity - 1)}
                    aria-label={`Уменьшить ${p.name}`}
                  >
                    Убавить
                  </button>
                  <span key={quantity}>{quantity}</span>
                  <button
                    disabled={quantity >= Math.min(p.stock, 99)}
                    onClick={() => change(p.id, quantity + 1)}
                    aria-label={`Увеличить ${p.name}`}
                  >
                    Добавить
                  </button>
                </div>
                <strong>{money(Number(p.price) * quantity)}</strong>
                <button
                  className={s.remove}
                  onClick={() => change(p.id, 0)}
                  aria-label={`Удалить ${p.name}`}
                >
                  Удалить
                </button>
              </article>
            ))}
            <Link to="/catalog" className={s.back}>
              Вернуться к покупкам
            </Link>
          </div>
          <aside className={s.summary} data-reveal="scale">
            <h2>Ваш заказ</h2>
            <div>
              <span>Товары · {count} шт.</span>
              <b>{money(total)}</b>
            </div>
            <div>
              <span>Доставка СДЭК</span>
              <span>На следующем шаге</span>
            </div>
            <div className={s.total}>
              <span>Итого</span>
              <strong key={total}>{money(total)}</strong>
            </div>
            <Link to="/checkout" className="button">
              Перейти к оформлению
            </Link>
            <p className={s.summaryNote}>
              <Truck size={16} /> Выберем удобный способ доставки
              <br />и покажем полную стоимость.
            </p>
            <p className={s.privacyNote}>
              Демонстрационный заказ. Реальные платежи и сбор персональных
              данных отключены.
            </p>
          </aside>
        </div>
      )}
    </div>
  );
}
