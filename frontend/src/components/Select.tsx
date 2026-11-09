import {
  Children,
  isValidElement,
  useEffect,
  useId,
  useRef,
  useState,
  type ReactNode,
  type KeyboardEvent,
} from "react";
import s from "./Select.module.scss";
type Props = {
  value: string;
  onChange: (event: { target: { value: string } }) => void;
  children: ReactNode;
  disabled?: boolean;
  "aria-label"?: string;
  id?: string;
  className?: string;
};
export default function Select({
  value,
  onChange,
  children,
  disabled = false,
  "aria-label": ariaLabel,
  id,
  className = "",
}: Props) {
  const generated = useId(),
    listId = generated + "-options",
    root = useRef<HTMLDivElement>(null),
    button = useRef<HTMLButtonElement>(null);
  const options = Children.toArray(children).flatMap((child) => {
    if (!isValidElement<{ value?: string; children?: ReactNode }>(child))
      return [];
    const label = String(child.props.children ?? "");
    return [{ value: child.props.value ?? label, label }];
  });
  const [open, setOpen] = useState(false),
    [cursor, setCursor] = useState(0);
  const selected = options.findIndex((o) => o.value === value);
  useEffect(() => {
    if (!open) return;
    const close = (e: PointerEvent) => {
      if (!root.current?.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener("pointerdown", close);
    return () => document.removeEventListener("pointerdown", close);
  }, [open]);
  function choose(index: number) {
    const option = options[index];
    if (option) onChange({ target: { value: option.value } });
    setOpen(false);
    button.current?.focus();
  }
  function keyboard(e: KeyboardEvent) {
    if (e.key === "Escape") {
      e.preventDefault();
      setOpen(false);
      return;
    }
    if (e.key === "Tab") {
      setOpen(false);
      return;
    }
    if (e.key === "ArrowDown" || e.key === "ArrowUp") {
      e.preventDefault();
      if (!open) {
        setOpen(true);
        setCursor(Math.max(0, selected));
      } else
        setCursor(
          (n) =>
            (n + (e.key === "ArrowDown" ? 1 : -1) + options.length) %
            options.length,
        );
    } else if (e.key === "Home" && open) {
      e.preventDefault();
      setCursor(0);
    } else if (e.key === "End" && open) {
      e.preventDefault();
      setCursor(options.length - 1);
    } else if ((e.key === "Enter" || e.key === " ") && open) {
      e.preventDefault();
      choose(cursor);
    } else if (e.key.length === 1 && e.key !== " ") {
      const next = options.findIndex((o) =>
        o.label.toLocaleLowerCase().startsWith(e.key.toLocaleLowerCase()),
      );
      if (next >= 0) {
        e.preventDefault();
        setCursor(next);
        if (!open) {
          setOpen(true);
        }
      }
    }
  }
  return (
    <div
      ref={root}
      className={`${s.select} ${className}`}
      onKeyDown={keyboard}
      onBlur={(e) => {
        if (!e.currentTarget.contains(e.relatedTarget)) setOpen(false);
      }}
    >
      <button
        ref={button}
        id={id}
        type="button"
        role="combobox"
        aria-label={ariaLabel}
        aria-haspopup="listbox"
        aria-expanded={open}
        aria-controls={listId}
        aria-activedescendant={open ? `${listId}-${cursor}` : undefined}
        disabled={disabled}
        onClick={() => {
          setOpen(!open);
          setCursor(Math.max(0, selected));
        }}
        className={s.trigger}
      >
        {options[selected]?.label || options[0]?.label || "Выберите"}
      </button>
      {open && (
        <div
          id={listId}
          className={s.list}
          role="listbox"
          aria-label={ariaLabel}
        >
          {options.map((option, i) => (
            <div
              key={option.value}
              id={`${listId}-${i}`}
              role="option"
              aria-selected={option.value === value}
              className={`${s.option} ${cursor === i ? s.focused : ""}`}
              onPointerMove={() => setCursor(i)}
              tabIndex={-1}
              onPointerDown={(e) => {
                if (e.pointerType === "mouse") e.preventDefault();
              }}
              onClick={() => choose(i)}
            >
              {option.label}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
