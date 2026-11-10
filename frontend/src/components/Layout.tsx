import { useEffect, useState } from "react";
import { Link, NavLink, Outlet, useLocation } from "react-router-dom";
import { Check } from "lucide-react";
import { usePageMotion } from "./usePageMotion";
import SearchBox from "./SearchBox";
import { useCart } from "../store";
import type { Config } from "../types";
import s from "./Layout.module.scss";
export function Logo() {
  return (
    <Link to="/" className={s.logo} aria-label="Крутящий момент — главная">
      <img src="/images/project-logo.png" width="44" height="44" alt="" />
      <span>
        крутящий
        <br />
        момент<span className={s.logoDot}>.</span>
      </span>
    </Link>
  );
}
export default function Layout({ config }: { config: Config }) {
  const { count, toast } = useCart();
  const [menu, setMenu] = useState(false);
  const [notification, setNotification] = useState("");
  const location = useLocation();
  usePageMotion(location.pathname + location.search);
  useEffect(() => {
    setMenu(false);
    window.scrollTo({ top: 0, behavior: "instant" });
  }, [location.pathname]);
  useEffect(() => {
    if (!toast) return;
    setNotification(toast);
    const timer = setTimeout(() => setNotification(""), 3200);
    return () => clearTimeout(timer);
  }, [toast, count]);
  return (
    <>
      <header className={s.header}>
        <div className={`container ${s.headerMain}`}>
          <Logo />
          <nav
            className={menu ? s.mobileOpen : ""}
            aria-label="Главная навигация"
          >
            <NavLink to="/catalog">Каталог запчастей</NavLink>
            <NavLink to="/delivery">Доставка и оплата</NavLink>
            <NavLink to="/about">О магазине</NavLink>
          </nav>
          <div className={s.headerActions}>
            <Link to="/cart" className={s.cart}>
              <span>Корзина</span>
              <b key={count}>{count}</b>
            </Link>
            <button
              className={s.menuButton}
              onClick={() => setMenu(!menu)}
              aria-label={menu ? "Закрыть меню" : "Открыть меню"}
              aria-expanded={menu}
            >
              {menu ? "Закрыть" : "Меню"}
            </button>
          </div>
        </div>
        <div className={`container ${s.searchRow}`}>
          <Link to="/catalog" className={s.catalogButton}>
            Каталог
          </Link>
          <SearchBox />
          <span className={s.searchHint}>
            Нужная деталь.
            <br />
            <b>Без лишних поисков.</b>
          </span>
        </div>
      </header>
      <main className={s.page}>
        <Outlet context={config} />
      </main>
      <footer className={s.footer}>
        <div className={`container ${s.footerTop}`}>
          <div>
            <Logo />
            <p>
              Для тех, кто любит
              <br />
              свой автомобиль.
            </p>
          </div>
          <div>
            <h3>Навигация</h3>
            <Link to="/catalog">Каталог запчастей</Link>
            <Link to="/delivery">Доставка и оплата</Link>
            <Link to="/about">О магазине</Link>
          </div>
          <div>
            <h3>По делу</h3>
            <Link to="/catalog?category=brakes">Тормозная система</Link>
            <Link to="/catalog?category=filters">Фильтры</Link>
            <Link to="/catalog?category=suspension">Подвеска и рулевое</Link>
          </div>
          <div className={s.studio}>
            <h3>
              Так может выглядеть
              <br />
              ваш интернет-магазин.
            </h3>
            <a
              href="https://nemida-studio.com/ru/"
              target="_blank"
              rel="noreferrer"
            >
              Обсудить с Триад Студио
            </a>
          </div>
        </div>
        <div className={`container ${s.footerBottom}`}>
          <p>
            Это демонстрационная версия, а не реальный коммерческий продукт.
            Сайт не собирает и не хранит персональные данные посетителей: в
            заказах используются вымышленные значения. Оплата и доставка
            имитируются. Для приобретения такого сайта обратитесь в
            <a
              href="https://nemida-studio.com/ru/"
              target="_blank"
              rel="noreferrer"
            >
              Триад Студио
            </a>
            .
          </p>
          <div>
            <span>© {new Date().getFullYear()} Крутящий момент</span>
            <a
              href="https://nemida-studio.com/ru/"
              target="_blank"
              rel="noreferrer"
            >
              Разраработано Триад Студио
            </a>
          </div>
        </div>
      </footer>
      {notification && (
        <div className={s.toast} role="status">
          <Check size={18} />
          <span>{notification}</span>
          <Link to="/cart">Открыть</Link>
        </div>
      )}
    </>
  );
}
