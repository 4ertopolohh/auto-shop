import { createContext, useContext, useState, type ReactNode } from "react";
import type { CartItem, Product } from "./types";
import { track } from "./api";
type Store = {
  items: CartItem[];
  add: (p: Product) => void;
  change: (id: number, quantity: number) => void;
  clear: () => void;
  count: number;
  total: number;
  toast: string;
};
const Context = createContext<Store | null>(null);
export function CartProvider({ children }: { children: ReactNode }) {
  // Cart is intentionally memory-only. No contact data or visitor IDs are persisted.
  const [items, setItems] = useState<CartItem[]>([]);
  const [toast, setToast] = useState("");
  function add(product: Product) {
    if (!product.stock) return;
    track("add_to_cart");
    setItems((current) => {
      const found = current.find((i) => i.product.id === product.id);
      return found
        ? current.map((i) =>
            i.product.id === product.id
              ? { ...i, quantity: Math.min(product.stock, 99, i.quantity + 1) }
              : i,
          )
        : [...current, { product, quantity: 1 }];
    });
    setToast(`${product.name} — в корзине`);
  }
  const value: Store = {
    items,
    add,
    change: (id, quantity) =>
      setItems((current) =>
        current.flatMap((i) =>
          i.product.id !== id
            ? [i]
            : quantity > 0
              ? [{ ...i, quantity: Math.min(i.product.stock, 99, quantity) }]
              : [],
        ),
      ),
    clear: () => setItems([]),
    count: items.reduce((n, i) => n + i.quantity, 0),
    total: items.reduce((n, i) => n + Number(i.product.price) * i.quantity, 0),
    toast,
  };
  return <Context value={value}>{children}</Context>;
}
export function useCart() {
  const value = useContext(Context);
  if (!value) throw new Error("CartProvider missing");
  return value;
}
