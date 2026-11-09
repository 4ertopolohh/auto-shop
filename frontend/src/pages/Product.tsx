import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { ShieldCheck, Truck } from "lucide-react";
import type { Product, ProductList } from "../types";
import { money, useResource } from "../api";
import { useCart } from "../store";
import { ErrorBox, Image, Loading, ProductCard } from "../components/UI";
import s from "./Product.module.scss";
export default function ProductPage() {
  const { slug } = useParams();
  const { data: p, error, retry } = useResource<Product>(`products/${slug}/`);
  const { data: related } = useResource<ProductList>(
    `products/?category=${p?.category || ""}`,
  );
  const [index, setIndex] = useState(0),
    [tab, setTab] = useState("specs");
  const { add, items, change } = useCart();
  useEffect(() => {
    setIndex(0);
  }, [slug]);
  useEffect(() => {
    if (p) {
      document.title = p.seo_title || `${p.brand} ${p.name} — Крутящий момент`;
      document
        .querySelector('meta[name="description"]')
        ?.setAttribute("content", p.seo_description || p.description);
    }
  }, [p]);
  if (error)
    return (
      <div className="container section">
        <ErrorBox message={error} retry={retry} />
      </div>
    );
  if (!p)
    return (
      <div className="container section">
        <Loading cards={2} />
      </div>
    );
  const quantity = items.find((i) => i.product.id === p.id)?.quantity || 0;
  return (
    <div className="container">
      <div className="breadcrumb">
        <Link to="/">Главная</Link>
        <Link to="/catalog">Каталог</Link>
        <Link to={`/catalog?category=${p.category}`}>{p.category_name}</Link>
        <span>{p.brand}</span>
      </div>
      <section className={s.product}>
        <div className={s.gallery}>
          <div
            className={s.mainImage}
            data-detail={
              p.images.length > 1 &&
              p.images.every((image) => image.url === p.images[0].url)
                ? index
                : 0
            }
          >
            {p.badge && <span className={s.badge}>{p.badge}</span>}
            <Image
              key={index}
              src={p.images[index]?.url}
              alt={p.images[index]?.alt || p.name}
              eager
            />
            <div className={s.galleryControls}>
              <button
                onClick={() =>
                  setIndex((index - 1 + p.images.length) % p.images.length)
                }
                aria-label="Предыдущее фото"
                disabled={p.images.length < 2}
              >
                Назад
              </button>
              <span>
                {index + 1} / {p.images.length}
              </span>
              <button
                onClick={() => setIndex((index + 1) % p.images.length)}
                aria-label="Следующее фото"
                disabled={p.images.length < 2}
              >
                Далее
              </button>
            </div>
          </div>
          <p className={s.photoNote}>
            Фотографии иллюстративные. Дополнительные миниатюры показывают
            детали исходного снимка.
          </p>
          <div className={s.thumbnails}>
            {p.images.map((image, i) => (
              <button
                key={`${image.url}-${i}`}
                className={index === i ? s.current : ""}
                onClick={() => setIndex(i)}
                aria-label={`Фото ${i + 1}`}
                aria-pressed={index === i}
              >
                <img
                  src={image.url}
                  alt=""
                  loading="lazy"
                  style={{
                    transform: `scale(${p.images.every((photo) => photo.url === p.images[0].url) ? 1 + i * 0.3 : 1})`,
                  }}
                />
              </button>
            ))}
            <span>
              Рассмотрите
              <br />
              каждую деталь.
            </span>
          </div>
        </div>
        <div className={s.info}>
          <h1>{p.name}</h1>
          <Link
            className={s.brand}
            to={`/catalog?brand=${encodeURIComponent(p.brand)}`}
          >
            {p.brand}
          </Link>
          <div className={s.article}>
            <span>
              Артикул: <b>{p.sku}</b>
            </span>
            <span>OEM: {p.oem || "Не указан"}</span>
          </div>
          <p className={s.description}>{p.description}</p>
          <div className={s.price}>
            <strong>{money(p.price)}</strong>
            {p.old_price && <del>{money(p.old_price)}</del>}
            <span>
              <i />
              {p.stock ? `В наличии · ${p.stock} шт.` : "Нет в наличии"}
            </span>
          </div>
          <div className={s.buy}>
            {quantity > 0 ? (
              <>
                <div className={s.quantity}>
                  <button
                    onClick={() => change(p.id, quantity - 1)}
                    aria-label="Уменьшить количество"
                  >
                    Убавить
                  </button>
                  <span>{quantity}</span>
                  <button
                    disabled={quantity >= p.stock}
                    onClick={() => change(p.id, quantity + 1)}
                    aria-label="Увеличить количество"
                  >
                    Добавить
                  </button>
                </div>
                <Link className="button" to="/cart">
                  В корзине
                </Link>
              </>
            ) : (
              <button
                className="button"
                disabled={!p.stock}
                onClick={() => add(p)}
              >
                Добавить в корзину
              </button>
            )}
          </div>
          <div className={s.delivery}>
            <div>
              <Truck size={19} />
              <div>
                <b>СДЭК — до пункта или до двери</b>
                <p>Стоимость и срок при оформлении</p>
              </div>
            </div>
            <div>
              <ShieldCheck size={19} />
              <div>
                <b>Уверенность в каждой детали</b>
                <p>Сверьте OEM и применимость перед покупкой</p>
              </div>
            </div>
          </div>
        </div>
      </section>
      <section className={s.details}>
        <div className={s.tabs} role="tablist" aria-label="Информация о товаре">
          {[
            ["specs", "Характеристики"],
            ["fit", "Совместимость"],
            ["delivery", "Доставка и оплата"],
          ].map(([id, label]) => (
            <button
              key={id}
              id={`tab-${id}`}
              role="tab"
              aria-selected={tab === id}
              aria-controls={`panel-${id}`}
              className={tab === id ? s.active : ""}
              onClick={() => setTab(id)}
            >
              {label}
            </button>
          ))}
        </div>
        <div
          className={s.tabPanel}
          role="tabpanel"
          id={`panel-${tab}`}
          aria-labelledby={`tab-${tab}`}
        >
          {tab === "specs" ? (
            <>
              <h2>Всё, что важно знать</h2>
              <dl>
                {Object.entries(p.specs).map(([key, value]) => (
                  <div key={key}>
                    <dt>{key}</dt>
                    <dd>{value}</dd>
                  </div>
                ))}
                <div>
                  <dt>Производитель</dt>
                  <dd>{p.brand}</dd>
                </div>
                <div>
                  <dt>Артикул</dt>
                  <dd>{p.sku}</dd>
                </div>
              </dl>
            </>
          ) : tab === "fit" ? (
            <>
              <h2>Подходит автомобилям</h2>
              <div className={s.fit}>
                {p.compatibility.map((c) => (
                  <div key={c.make + c.model}>
                    <b>
                      {c.make} {c.model}
                    </b>
                    <span>{c.years}</span>
                  </div>
                ))}
              </div>
              <p className={s.fitNote}>
                Применимость приведена для демонстрации подбора. Это не
                техническая рекомендация. Перед реальной покупкой сверяйте VIN,
                OEM-номер и комплектацию.
              </p>
            </>
          ) : (
            <>
              <h2>Детали уже в пути</h2>
              <p>
                Выберите пункт выдачи СДЭК или курьерскую доставку на странице
                оформления. Оплата через ЮKassa. В этой демонстрационной версии
                деньги не списываются, отправления не создаются.
              </p>
              <Link className="textLink" to="/delivery">
                Подробнее о доставке
              </Link>
            </>
          )}
        </div>
      </section>
      {related && related.results.some((item) => item.id !== p.id) && (
        <section className={s.related}>
          <div className="sectionHeading">
            <h2>Ещё в этом разделе</h2>
            <Link to={`/catalog?category=${p.category}`}>В каталог </Link>
          </div>
          <div className="productGrid">
            {related.results
              .filter((item) => item.id !== p.id)
              .slice(0, 4)
              .map((item) => (
                <ProductCard product={item} key={item.id} />
              ))}
          </div>
        </section>
      )}
    </div>
  );
}
