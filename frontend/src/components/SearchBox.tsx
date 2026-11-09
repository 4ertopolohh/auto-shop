import { useEffect, useId, useRef, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Search } from "lucide-react";
import { money, request } from "../api";
import type { Product, ProductList } from "../types";
import s from "./SearchBox.module.scss";
export default function SearchBox() {
  const [query, setQuery] = useState(""),
    [open, setOpen] = useState(false),
    [results, setResults] = useState<Product[]>([]),
    [loading, setLoading] = useState(false),
    [selected, setSelected] = useState(-1),
    [failed, setFailed] = useState(false);
  const root = useRef<HTMLFormElement>(null),
    id = useId(),
    navigate = useNavigate();
  useEffect(() => {
    if (!open || query.trim().length < 2) {
      setResults([]);
      setLoading(false);
      setFailed(false);
      return;
    }
    const controller = new AbortController();
    setResults([]);
    setSelected(-1);
    setLoading(true);
    setFailed(false);
    const timer = setTimeout(() => {
      request<ProductList>("products/?q=" + encodeURIComponent(query.trim()), {
        signal: controller.signal,
      })
        .then((data) => {
          setResults(data.results.slice(0, 5));
          setSelected(-1);
          setLoading(false);
        })
        .catch((error: Error) => {
          if (error.name !== "AbortError") {
            setLoading(false);
            setFailed(true);
          }
        });
    }, 220);
    return () => {
      clearTimeout(timer);
      controller.abort();
    };
  }, [query, open]);
  useEffect(() => {
    const outside = (event: PointerEvent) => {
      if (!root.current?.contains(event.target as Node)) setOpen(false);
    };
    document.addEventListener("pointerdown", outside);
    return () => document.removeEventListener("pointerdown", outside);
  }, []);
  function search() {
    setOpen(false);
    navigate("/catalog?q=" + encodeURIComponent(query.trim()));
  }
  return (
    <form
      ref={root}
      className={s.search}
      role="search"
      onSubmit={(event) => {
        event.preventDefault();
        if (!loading && selected >= 0 && results[selected]) {
          navigate("/product/" + results[selected].slug);
          setOpen(false);
        } else search();
      }}
      onBlur={(event) => {
        if (!event.currentTarget.contains(event.relatedTarget)) setOpen(false);
      }}
    >
      <Search size={18} aria-hidden="true" />
      <input
        role="combobox"
        aria-label="Поиск по названию, артикулу или OEM"
        aria-autocomplete="list"
        aria-expanded={open}
        aria-controls={id}
        aria-activedescendant={selected >= 0 ? id + "-" + selected : undefined}
        autoComplete="off"
        placeholder="Название детали, артикул или OEM-номер"
        value={query}
        onFocus={() => setOpen(true)}
        onChange={(event) => {
          setQuery(event.target.value);
          setSelected(-1);
          setOpen(true);
        }}
        onKeyDown={(event) => {
          if (event.key === "Escape") {
            setOpen(false);
            setSelected(-1);
          }
          if (event.key === "ArrowDown" && !loading && results.length) {
            event.preventDefault();
            setOpen(true);
            setSelected((i) => (i + 1) % results.length);
          }
          if (event.key === "ArrowUp" && !loading && results.length) {
            event.preventDefault();
            setSelected((i) => (i - 1 + results.length) % results.length);
          }
        }}
      />
      <button aria-label="Найти запчасть">Найти</button>
      {open && (
        <div
          className={s.suggestions}
          id={id}
          role="listbox"
          aria-label="Подсказки поиска"
        >
          {query.trim().length < 2 ? (
            <>
              {["Тормозной диск", "Масляный фильтр", "Свеча зажигания"].map(
                (text) => (
                  <Link
                    key={text}
                    role="option"
                    aria-selected={false}
                    to={"/catalog?q=" + encodeURIComponent(text)}
                    onClick={() => {
                      setQuery(text);
                      setOpen(false);
                    }}
                  >
                    {text}
                  </Link>
                ),
              )}
            </>
          ) : loading ? (
            <p role="status">Ищем подходящие детали…</p>
          ) : results.length ? (
            <>
              {results.map((p, i) => (
                <Link
                  key={p.id}
                  id={id + "-" + i}
                  role="option"
                  aria-selected={selected === i}
                  to={"/product/" + p.slug}
                  onPointerMove={() => setSelected(i)}
                  onClick={() => setOpen(false)}
                >
                  <img src={p.images[0]?.url} alt="" />
                  <span>
                    <b>{p.name}</b>
                    <small>
                      {p.brand} · {p.sku}
                    </small>
                  </span>
                  <strong>{money(p.price)}</strong>
                </Link>
              ))}
              <button type="button" className={s.all} onClick={search}>
                Показать все результаты
              </button>
            </>
          ) : (
            <p>
              {failed
                ? "Подсказки недоступны. Нажмите «Найти», чтобы открыть каталог."
                : "Совпадений нет. Попробуйте другой артикул или название."}
            </p>
          )}
        </div>
      )}
    </form>
  );
}
