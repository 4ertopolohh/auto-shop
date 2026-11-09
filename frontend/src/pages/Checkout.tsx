import Select from "../components/Select";
import { useRef, useState } from "react";
import { Link } from "react-router-dom";
import {
  Check,
  CheckCircle2,
  CreditCard,
  LockKeyhole,
  MapPin,
  Package,
  Truck,
  XCircle,
} from "lucide-react";
import { useCart } from "../store";
import { money, request, useResource, track } from "../api";
import type { DeliveryPoint, Order } from "../types";
import { Empty, ErrorBox } from "../components/UI";
import s from "./Commerce.module.scss";
export default function Checkout() {
  const { items, count, total, clear } = useCart();
  const { data, error, retry } = useResource<{ points: DeliveryPoint[] }>(
    "delivery/",
  );
  const [city, setCity] = useState("Москва"),
    [point, setPoint] = useState("MSK-01"),
    [delivery, setDelivery] = useState("pickup");
  const [order, setOrder] = useState<Order | null>(null),
    [busy, setBusy] = useState(false),
    [message, setMessage] = useState("");
  const key = useRef(crypto.randomUUID());
  const chosen = data?.points.find((p) => p.id === point);
  const shipping = (chosen?.price || 350) + (delivery === "courier" ? 200 : 0);
  async function create() {
    setBusy(true);
    setMessage("");
    try {
      const value = await request<Order>("checkout/", {
        method: "POST",
        body: JSON.stringify({
          items: items.map((i) => ({ id: i.product.id, quantity: i.quantity })),
          delivery,
          point,
          idempotency_key: key.current,
        }),
      });
      setOrder(value);
      track("begin_checkout");
    } catch (e) {
      setMessage((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  async function pay(outcome: "success" | "failure" | "cancel") {
    if (!order) return;
    setBusy(true);
    setMessage("");
    try {
      const value = await request<Order>(`orders/${order.id}/payment/`, {
        method: "POST",
        body: JSON.stringify({ outcome }),
      });
      setOrder(value);
      if (value.status === "paid") {
        clear();
        track("purchase");
      }
    } catch (e) {
      setMessage((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  if (order?.status === "paid" || order?.status === "cancelled")
    return (
      <div className={`container ${s.success}`}>
        <span className={s.successIcon}>
          {order.status === "paid" ? (
            <CheckCircle2 size={44} />
          ) : (
            <Package size={44} />
          )}
        </span>
        <h1 className="pageTitle">
          {order.status === "paid"
            ? "Всё сошлось. Заказ оформлен."
            : "Заказ отменён."}
        </h1>
        <p>
          {order.status === "paid"
            ? "Вы прошли весь путь покупки. Платёж подтверждён в демонстрационном режиме, деньги не списаны и отправление не создано."
            : "Оплата не выполнена. Вы можете вернуться к корзине и оформить новый заказ."}
        </p>
        <div className={s.receipt}>
          <div>
            <span>Получатель</span>
            <b>{order.recipient}</b>
          </div>
          <div>
            <span>Доставка</span>
            <b>{order.destination}</b>
          </div>
          <div>
            <span>Сумма заказа</span>
            <b>{money(order.total)}</b>
          </div>
          <div>
            <span>Статус</span>
            <b>{order.status === "paid" ? "Оплачен · имитация" : "Отменён"}</b>
          </div>
        </div>
        <Link
          to={order.status === "paid" ? "/catalog" : "/cart"}
          className="button"
          onClick={() => {
            if (order.status === "cancelled") {
              setOrder(null);
              key.current = crypto.randomUUID();
            }
          }}
        >
          Продолжить
        </Link>
      </div>
    );
  if (!items.length && !order)
    return (
      <div className="container section">
        <Empty title="Сначала выберите детали">
          <p>Добавьте товары в корзину, чтобы оформить заказ.</p>
          <Link to="/catalog" className="button">
            Открыть каталог
          </Link>
        </Empty>
      </div>
    );
  return (
    <div className="container">
      <div className="breadcrumb">
        <Link to="/">Главная</Link>
        <Link to="/cart">Корзина</Link>
        <span>Оформление</span>
      </div>
      <h1 className="pageTitle">Осталось совсем немного.</h1>
      <p className={s.subtitle}>
        Выберите доставку. Мы уже позаботились об остальном.
      </p>
      <div className={s.steps}>
        <span className={s.done}>
          <Check size={13} /> Корзина
        </span>
        <i />
        <span className={!order ? s.current : s.done}>02 / Доставка</span>
        <i />
        <span className={order ? s.current : ""}>03 / Оплата</span>
      </div>
      {message && (
        <p className={s.error} role="alert">
          {message}
        </p>
      )}
      <div className={s.layout}>
        <div>
          {!order ? (
            <>
              <section className={s.checkoutSection}>
                <div className={s.sectionTitle}>
                  <h2>Кому доставить</h2>
                  <LockKeyhole size={16} />
                </div>
                <p className={s.demoNote}>
                  Можно пройти оформление без личных данных. Получатель
                  вымышленный, поля защищены от ввода. Сайт не отправляет и не
                  сохраняет реальные контакты.
                </p>
                <div className={s.fields}>
                  <label className="field">
                    Получатель
                    <input
                      value="Алексей Демонстрационный"
                      readOnly
                      autoComplete="off"
                    />
                  </label>
                  <label className="field">
                    Телефон
                    <input
                      value="+7 (000) 000-00-00"
                      readOnly
                      autoComplete="off"
                    />
                  </label>
                  <label className="field">
                    Электронная почта
                    <input
                      value="buyer@example.invalid"
                      readOnly
                      autoComplete="off"
                    />
                  </label>
                </div>
              </section>
              <section className={s.checkoutSection}>
                <div className={s.sectionTitle}>
                  <h2>Как вам удобнее?</h2>
                  <Truck size={18} />
                </div>
                <div className={s.methods}>
                  <button
                    aria-pressed={delivery === "pickup"}
                    className={delivery === "pickup" ? s.chosen : ""}
                    onClick={() => setDelivery("pickup")}
                  >
                    <b>Пункт выдачи СДЭК</b>
                    <span>Заберите по пути</span>
                  </button>
                  <button
                    aria-pressed={delivery === "courier"}
                    className={delivery === "courier" ? s.chosen : ""}
                    onClick={() => setDelivery("courier")}
                  >
                    <b>Курьер СДЭК</b>
                    <span>Привезём до двери</span>
                  </button>
                </div>
                {error ? (
                  <ErrorBox message={error} retry={retry} />
                ) : !data ? (
                  <p className={s.demoNote}>Загружаем варианты доставки…</p>
                ) : (
                  <>
                    <div className={`field ${s.city}`}>
                      <span>Город</span>
                      <Select
                        aria-label="Город"
                        value={city}
                        onChange={(e) => {
                          setCity(e.target.value);
                          const first = data.points.find(
                            (p) => p.city === e.target.value,
                          );
                          if (first) setPoint(first.id);
                        }}
                      >
                        {[...new Set(data.points.map((p) => p.city))].map(
                          (c) => (
                            <option key={c}>{c}</option>
                          ),
                        )}
                      </Select>
                    </div>
                    {delivery === "pickup" ? (
                      <div className={s.points}>
                        {data.points
                          .filter((p) => p.city === city)
                          .map((p) => (
                            <button
                              key={p.id}
                              onClick={() => setPoint(p.id)}
                              className={point === p.id ? s.chosen : ""}
                              aria-pressed={point === p.id}
                            >
                              <span>
                                <b>{p.label}</b>
                                <span>{p.address}</span>
                                <small>{p.hours}</small>
                              </span>
                              <span>
                                <b>{money(p.price)}</b>
                                <small>{p.days}</small>
                              </span>
                            </button>
                          ))}
                      </div>
                    ) : (
                      <div className={s.courierAddress}>
                        <MapPin size={20} />
                        <span>
                          <b>{city}, ул. Демонстрационная, 10</b>
                          <p>Вымышленный адрес для проверки сценария</p>
                        </span>
                      </div>
                    )}
                    <p className={s.demoNote}>
                      Пункты и тарифы здесь демонстрационные. Реальные заявки в
                      СДЭК не отправляются.
                    </p>
                  </>
                )}
              </section>
            </>
          ) : (
            <section className={s.checkoutSection}>
              <div className={s.sectionTitle}>
                <h2>Оплата заказа</h2>
                <CreditCard size={19} />
              </div>
              <div className={s.paymentBrand}>
                <span>
                  Ю<span>Kassa</span>
                </span>
                <LockKeyhole size={20} />
              </div>
              <h3 className={s.paymentTitle}>Проверим финальный шаг.</h3>
              <p className={s.demoNote}>
                Это имитация платёжной страницы. Банковская карта и её реквизиты
                не нужны. Выберите результат, чтобы проверить поведение
                магазина.
              </p>
              {order.status === "failed" && (
                <div className={s.paymentFailure} role="alert">
                  <XCircle size={19} />
                  <span>
                    Оплата не прошла. Заказ сохранён, можно повторить попытку.
                  </span>
                </div>
              )}
              <div className={s.paymentActions}>
                <button
                  className="button"
                  disabled={busy}
                  onClick={() => pay("success")}
                >
                  {busy ? "Обрабатываем…" : "Успешная оплата"}
                </button>
                <button
                  className="button outline"
                  disabled={busy}
                  onClick={() => pay("failure")}
                >
                  Проверить отказ
                </button>
                <button
                  className={s.cancel}
                  disabled={busy}
                  onClick={() => pay("cancel")}
                >
                  Отменить оплату
                </button>
              </div>
              <div className={s.receipt}>
                <div>
                  <span>Номер заказа</span>
                  <b>{order.number}</b>
                </div>
                <div>
                  <span>Получатель</span>
                  <b>{order.recipient}</b>
                </div>
                <div>
                  <span>Адрес</span>
                  <b>{order.destination}</b>
                </div>
              </div>
            </section>
          )}
        </div>
        <aside className={s.summary}>
          <h2>Ваш заказ</h2>
          <div>
            <span>Товары · {count} шт.</span>
            <b>{money(total)}</b>
          </div>
          {items.map((i) => (
            <div className={s.miniItem} key={i.product.id}>
              <span>
                {i.product.name} × {i.quantity}
              </span>
              <b>{money(Number(i.product.price) * i.quantity)}</b>
            </div>
          ))}
          <div>
            <span>Доставка СДЭК</span>
            <b>{money(order?.delivery_price || shipping)}</b>
          </div>
          <div className={s.total}>
            <span>Итого</span>
            <strong>{money(order?.total || total + shipping)}</strong>
          </div>
          {!order && (
            <button
              className="button"
              disabled={busy || !data || !!error}
              onClick={create}
            >
              {busy ? "Оформляем…" : "Перейти к оплате"}
            </button>
          )}
          <p className={s.summaryNote}>
            <LockKeyhole size={15} /> Без реальных списаний
            <br />и персональных данных
          </p>
          <p className={s.privacyNote}>
            Продолжая, вы создаёте демонстрационный заказ с вымышленными
            контактами.
          </p>
        </aside>
      </div>
      <Link to="/cart" className={s.back}>
        Вернуться в корзину
      </Link>
    </div>
  );
}
