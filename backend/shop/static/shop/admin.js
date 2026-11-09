(() => {
  "use strict";
  const initialized = new WeakSet();
  let counter = 0;
  function customSelect(native) {
    if (initialized.has(native) || native.closest(".selector,.empty-form"))
      return;
    initialized.add(native);
    const root = document.createElement("span");
    root.className = "km-select";
    const trigger = document.createElement("button");
    trigger.type = "button";
    trigger.className = "km-select-trigger";
    trigger.setAttribute("role", "combobox");
    trigger.setAttribute("aria-haspopup", "listbox");
    trigger.setAttribute("aria-expanded", "false");
    const labelNode = native.labels?.[0]?.cloneNode(true);
    labelNode
      ?.querySelectorAll("select,.km-select")
      .forEach((element) => element.remove());
    const label =
      labelNode?.textContent?.trim().replace(/:$/, "") ||
      native.getAttribute("aria-label") ||
      "Выберите значение";
    trigger.setAttribute("aria-label", label);
    const list = document.createElement("span");
    list.className = "km-select-list";
    list.id = "km-options-" + ++counter;
    list.setAttribute("role", "listbox");
    list.hidden = true;
    trigger.setAttribute("aria-controls", list.id);
    native.before(root);
    root.append(native, trigger, list);
    native.classList.add("km-native-select");
    native.tabIndex = -1;
    native.setAttribute("aria-hidden", "true");
    const sync = () => {
      trigger.textContent =
        [...native.selectedOptions]
          .map((o) => (/^-+$/.test(o.text.trim()) ? "Выберите" : o.text))
          .join(", ") || "Выберите";
      trigger.disabled = native.disabled;
      list.replaceChildren();
      [...native.options].forEach((option, index) => {
        const item = document.createElement("span");
        item.className = "km-select-option";
        item.setAttribute("role", "option");
        item.setAttribute("aria-selected", String(option.selected));
        item.tabIndex = -1;
        item.textContent = /^-+$/.test(option.text.trim())
          ? "Выберите"
          : option.text;
        item.addEventListener("click", () => {
          if (option.disabled) return;
          if (native.multiple) option.selected = !option.selected;
          else native.selectedIndex = index;
          native.dispatchEvent(new Event("change", { bubbles: true }));
          if (!native.multiple) close();
          else sync();
          trigger.focus();
        });
        list.append(item);
      });
    };
    const close = () => {
      list.hidden = true;
      trigger.setAttribute("aria-expanded", "false");
    };
    trigger.addEventListener("click", () => {
      const opening = list.hidden;
      close();
      if (opening) {
        sync();
        list.hidden = false;
        trigger.setAttribute("aria-expanded", "true");
      }
    });
    root.addEventListener("keydown", (event) => {
      if (event.key === "Escape") {
        event.preventDefault();
        close();
        trigger.focus();
      }
      if (event.key === "Tab") close();
      if (["ArrowDown", "ArrowUp", "Home", "End"].includes(event.key)) {
        event.preventDefault();
        if (list.hidden) {
          sync();
          list.hidden = false;
          trigger.setAttribute("aria-expanded", "true");
        }
        const options = [...list.children];
        let index = options.indexOf(document.activeElement);
        if (event.key === "Home") index = 0;
        else if (event.key === "End") index = options.length - 1;
        else
          index =
            (index + (event.key === "ArrowDown" ? 1 : -1) + options.length) %
            options.length;
        options[index]?.focus();
      }
      if (
        (event.key === "Enter" || event.key === " ") &&
        document.activeElement?.getAttribute("role") === "option"
      ) {
        event.preventDefault();
        document.activeElement.click();
      }
    });
    document.addEventListener("pointerdown", (event) => {
      if (!root.contains(event.target)) close();
    });
    root.addEventListener("focusout", (event) => {
      if (!root.contains(event.relatedTarget)) close();
    });
    native.addEventListener("change", sync);
    sync();
    native.addEventListener("invalid", (event) => {
      event.preventDefault();
      trigger.focus();
      trigger.setAttribute("aria-invalid", "true");
    });
  }
  function customFile(native) {
    if (initialized.has(native) || native.closest(".empty-form")) return;
    initialized.add(native);
    const root = document.createElement("span");
    root.className = "km-file";
    const button = document.createElement("button");
    button.type = "button";
    button.textContent = native.multiple ? "Выбрать файлы" : "Выбрать файл";
    const name = document.createElement("span");
    name.textContent = "Файл не выбран";
    name.setAttribute("aria-live", "polite");
    native.before(root);
    root.append(native, button, name);
    native.classList.add("km-native-file");
    native.tabIndex = -1;
    native.setAttribute("aria-hidden", "true");
    button.addEventListener("click", () => native.click());
    native.addEventListener("change", () => {
      name.textContent =
        [...native.files].map((f) => f.name).join(", ") || "Файл не выбран";
    });
    native.addEventListener("invalid", (event) => {
      event.preventDefault();
      name.textContent = "Выберите файл перед продолжением";
      button.focus();
    });
    root.addEventListener("dragover", (event) => {
      event.preventDefault();
      root.classList.add("dragging");
    });
    root.addEventListener("dragleave", () => root.classList.remove("dragging"));
    root.addEventListener("drop", (event) => {
      event.preventDefault();
      root.classList.remove("dragging");
      if (event.dataTransfer?.files.length) {
        native.files = event.dataTransfer.files;
        native.dispatchEvent(new Event("change", { bubbles: true }));
      }
    });
  }
  function enhance() {
    document.querySelectorAll(".inline-deletelink").forEach((link) => {
      link.textContent = "Убрать";
    });
    document
      .querySelectorAll(".related-widget-wrapper-link")
      .forEach((link) => {
        if (link.dataset.km) return;
        const label = link.classList.contains("add-related")
          ? "Добавить"
          : link.classList.contains("change-related")
            ? "Изменить"
            : link.classList.contains("delete-related")
              ? "Удалить"
              : "Просмотр";
        link.replaceChildren(document.createTextNode(label));
        link.dataset.km = "1";
      });
    document.querySelectorAll("select").forEach(customSelect);
    document.querySelectorAll("input[type=file]").forEach(customFile);
    const theme = document.querySelector(".theme-toggle");
    if (theme && !theme.dataset.km) {
      theme.append("Тема");
      theme.dataset.km = "1";
    }
    const sidebar = document.querySelector("#toggle-nav-sidebar");
    if (sidebar && !sidebar.dataset.km) {
      sidebar.textContent = "Навигация";
      sidebar.dataset.km = "1";
    }
  }
  enhance();
  new MutationObserver((records) => {
    if (
      records.some((r) =>
        [...r.addedNodes].some(
          (n) =>
            n.nodeType === 1 &&
            (n.matches?.("select,input[type=file]") ||
              n.querySelector?.("select,input[type=file]")),
        ),
      )
    )
      enhance();
  }).observe(document.body, { childList: true, subtree: true });
})();
