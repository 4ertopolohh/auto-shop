import { useEffect } from "react";

/** Enhances existing semantic content, including asynchronously inserted results. */
export function usePageMotion(route: string) {
  useEffect(() => {
    const reduced = matchMedia("(prefers-reduced-motion: reduce)");
    if (reduced.matches || !("IntersectionObserver" in window)) return;
    const root = document.querySelector("main");
    if (!root) return;
    const prepared = new Set<HTMLElement>();
    let parallax: HTMLElement[] = [];
    const variants = ["up", "left", "scale", "down", "right"];
    const observer = new IntersectionObserver(entries => {
      for (const entry of entries) if (entry.isIntersecting) {
        const el = entry.target as HTMLElement;
        el.dataset.visible = "true";
        observer.unobserve(el);
      }
    }, { threshold: 0.08, rootMargin: "0px 0px -24px 0px" });
    const prepare = () => {
      parallax = Array.from(root.querySelectorAll<HTMLElement>("[data-parallax]"));
      root.querySelectorAll<HTMLElement>("h1, .sectionHeading, section > h2, article, form > section, [data-reveal], .productGrid > *").forEach(el => {
        if (prepared.has(el)) return;
        prepared.add(el);
        // No nested reveals: one transform per visual group.
        if (el.parentElement?.closest("[data-motion]")) return;
        el.dataset.motion = el.dataset.reveal || (el.matches("h1, .sectionHeading") ? "clip" : variants[prepared.size % variants.length]);
        const siblings = el.parentElement ? Array.from(el.parentElement.children) : [];
        el.style.setProperty("--reveal-delay", `${Math.min(siblings.indexOf(el) % 6, 5) * 85}ms`);
        observer.observe(el);
      });
    };
    prepare();
    const mutations = new MutationObserver(prepare);
    mutations.observe(root, { childList: true, subtree: true });
    let raf = 0;

    const update = () => {
      raf = 0;
      if (reduced.matches) return;
      const amplitude = matchMedia("(max-width:700px)").matches ? 8 : 24;
      for (const el of parallax) {
        const rect = el.getBoundingClientRect();
        if (rect.bottom < 0 || rect.top > innerHeight) continue;
        const progress = Math.max(-1, Math.min(1, (rect.top + rect.height / 2 - innerHeight / 2) / innerHeight));
        el.style.setProperty("--parallax", `${progress * amplitude * Number(el.dataset.parallax || 1)}px`);
      }
    };
    const scroll = () => { if (!raf) raf = requestAnimationFrame(update); };
    const revealAll = () => {
      if (reduced.matches) for (const el of prepared) el.dataset.visible = "true";
      scroll();
    };
    const focus = (event: Event) => {
      (event.target as HTMLElement).closest<HTMLElement>("[data-motion]")?.setAttribute("data-visible", "true");
    };
    root.addEventListener("focusin", focus);
    window.addEventListener("scroll", scroll, { passive: true });
    window.addEventListener("resize", scroll);
    reduced.addEventListener("change", revealAll);
    update();
    return () => {
      root.removeEventListener("focusin", focus);
      observer.disconnect(); mutations.disconnect(); cancelAnimationFrame(raf);
      window.removeEventListener("scroll", scroll); window.removeEventListener("resize", scroll);
      reduced.removeEventListener("change", revealAll);
      for (const el of prepared) { delete el.dataset.motion; delete el.dataset.visible; }
    };
  }, [route]);
}
