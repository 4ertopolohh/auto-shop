import Select from "../components/Select";
import { useState } from "react";
import { Link, useOutletContext, useSearchParams } from "react-router-dom";

import type { Config, ProductList } from "../types";
import { useResource } from "../api";
import { Loading, ErrorBox, Empty, ProductCard } from "../components/UI";
import s from "./Catalog.module.scss";
export default function Catalog() {
  const config = useOutletContext<Config>();
  const [params, setParams] = useSearchParams();
  const [filters, setFilters] = useState(false);
  const { data, error, retry } = useResource<ProductList>(
    "products/?" + params.toString(),
  );
  const update = (key: string, value: string) => {
    const next = new URLSearchParams(params);
    if (value) next.set(key, value);
    else next.delete(key);
    if (key !== "page") next.delete("page");
    setParams(next);
  };
  const make = params.get("make") || "",
    category = params.get("category") || "",
    title =
      config.categories.find((c) => c.slug === category)?.name ||
      "Каталог запчастей";
  return (
    <div className="container">
      <div className="breadcrumb">
        <Link to="/">Главная</Link>
        <span>Каталог</span>
      </div>
      <div className={s.heading}>
        <div>
          <h1 className="pageTitle">
            {title}
            <span>{data?.count ?? "—"}</span>
          </h1>
          <p className="muted">
            Подберите то, что подходит именно вашему автомобилю.
          </p>
        </div>
      </div>
      <div className={s.categories}>
        <button
          className={!category ? s.selected : ""}
          onClick={() => update("category", "")}
        >
          Все запчасти
        </button>
        {config.categories.map((c) => (
          <button
            className={category === c.slug ? s.selected : ""}
            key={c.slug}
            onClick={() => update("category", c.slug)}
          >
            {c.name}
          </button>
        ))}
      </div>
      <div className={s.layout}>
        <aside className={`${s.sidebar} ${filters ? s.show : ""}`}>
          <div className={s.filterHeading}>
            <h2>Уточним детали</h2>
            <button
              onClick={() => setFilters(false)}
              aria-label="Закрыть фильтры"
            >
              Закрыть
            </button>
          </div>
          <div className={s.filterGroup}>
            <h3>Ваш автомобиль</h3>
            <div className="field">
              <span>Марка</span>
              <Select
                aria-label="Марка"
                value={make}
                onChange={(e) => {
                  const n = new URLSearchParams(params);
                  n.delete("model");
                  n.delete("page");
                  if (e.target.value) n.set("make", e.target.value);
                  else n.delete("make");
                  setParams(n);
                }}
              >
                <option value="">Все марки</option>
                {[...new Set(config.vehicles.map((v) => v[0]))].map((v) => (
                  <option key={v}>{v}</option>
                ))}
              </Select>
            </div>
            <div className="field">
              <span>Модель</span>
              <Select
                aria-label="Модель"
                value={params.get("model") || ""}
                onChange={(e) => update("model", e.target.value)}
                disabled={!make}
              >
                <option value="">Все модели</option>
                {config.vehicles
                  .filter((v) => v[0] === make)
                  .map((v) => (
                    <option key={v[1]}>{v[1]}</option>
                  ))}
              </Select>
            </div>
            <p className={s.note}>
              Совместимость в каталоге носит иллюстративный характер. Перед
              реальной покупкой необходима проверка по VIN и OEM.
            </p>
          </div>
          <div className={s.filterGroup}>
            <h3>Стоимость, ₽</h3>
            <form
              className={s.priceRange}
              key={`${params.get("min")}-${params.get("max")}`}
              onSubmit={(e) => {
                e.preventDefault();
                const f = new FormData(e.currentTarget),
                  n = new URLSearchParams(params);
                for (const k of ["min", "max"]) {
                  const v = String(f.get(k) || "");
                  if (v) n.set(k, v);
                  else n.delete(k);
                }
                n.delete("page");
                setParams(n);
              }}
            >
              <input
                name="min"
                type="number"
                min="0"
                placeholder="От"
                aria-label="Цена от"
                defaultValue={params.get("min") || ""}
              />
              <span>—</span>
              <input
                name="max"
                type="number"
                min="0"
                placeholder="До"
                aria-label="Цена до"
                defaultValue={params.get("max") || ""}
              />
              <button aria-label="Применить цену">Применить</button>
            </form>
          </div>
          <div className={s.filterGroup}>
            <h3>Производитель</h3>
            <Select
              aria-label="Бренд"
              value={params.get("brand") || ""}
              onChange={(e) => update("brand", e.target.value)}
            >
              <option value="">Все бренды</option>
              {config.brands.map((b) => (
                <option key={b}>{b}</option>
              ))}
            </Select>
          </div>
          <label className={s.checkbox}>
            <input
              type="checkbox"
              checked={params.get("stock") === "1"}
              onChange={(e) => update("stock", e.target.checked ? "1" : "")}
            />
            <span>Только в наличии</span>
          </label>
          <button className={s.reset} onClick={() => setParams({})}>
            Сбросить все фильтры
          </button>
          <div className={s.help}>
            <span>Не знаете артикул?</span>
            <p>Начните с узла автомобиля — так проще найти нужный раздел.</p>
            <Link to="/">Подбор на схеме </Link>
          </div>
        </aside>
        <div className={s.results}>
          <div className={s.toolbar}>
            <span>
              {data ? `Найдено: ${data.count}` : "Ищем запчасти…"}
              {params.get("q") && ` · «${params.get("q")}»`}
            </span>
            <button
              className={s.filtersButton}
              onClick={() => setFilters(!filters)}
            >
              Фильтры
            </button>
            <div className={s.sort}>
              <span>Сортировка</span>
              <Select
                aria-label="Сортировка"
                value={params.get("sort") || ""}
                onChange={(e) => update("sort", e.target.value)}
              >
                <option value="">По умолчанию</option>
                <option value="price">Сначала дешевле</option>
                <option value="-price">Сначала дороже</option>
                <option value="name">По названию</option>
                <option value="new">По новизне</option>
              </Select>
            </div>
          </div>
          {error ? (
            <ErrorBox message={error} retry={retry} />
          ) : !data ? (
            <Loading cards={6} />
          ) : data.results.length ? (
            <>
              <div className={s.grid}>
                {data.results.map((p) => (
                  <ProductCard product={p} key={p.id} />
                ))}
              </div>
              {data.count > 12 && (
                <div className={s.pagination}>
                  <button
                    disabled={data.page <= 1}
                    onClick={() => update("page", String(data.page - 1))}
                    aria-label="Предыдущая страница"
                  >
                    Назад
                  </button>
                  <span>
                    {data.page} / {Math.ceil(data.count / 12)}
                  </span>
                  <button
                    disabled={data.page >= Math.ceil(data.count / 12)}
                    onClick={() => {
                      update("page", String(data.page + 1));
                      window.scrollTo({ top: 180, behavior: "smooth" });
                    }}
                    aria-label="Следующая страница"
                  >
                    Далее
                  </button>
                </div>
              )}
            </>
          ) : (
            <Empty title="Такой детали пока не нашлось">
              <p>Попробуйте другой артикул или измените фильтры.</p>
              <button className="button" onClick={() => setParams({})}>
                Показать все запчасти
              </button>
            </Empty>
          )}
        </div>
      </div>
    </div>
  );
}
