"use client";

import { useEffect, useId, useRef } from "react";
import { X } from "lucide-react";

export type ModalProps = {
  title: string;
  close: () => void;
  children: React.ReactNode;
};

type ModalEntry = {
  element: HTMLElement;
  close: () => void;
  previousFocus: HTMLElement | null;
};

const modalStack: ModalEntry[] = [];
let previousBodyOverflow = "";

function focusableElements(container: HTMLElement) {
  return Array.from(
    container.querySelectorAll<HTMLElement>(
      'a[href], button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])',
    ),
  ).filter((element) => element.getClientRects().length > 0);
}

export function Modal({
  title,
  close,
  children,
}: ModalProps) {
  const titleId = useId();
  const closeRef = useRef<HTMLButtonElement>(null);
  const modalRef = useRef<HTMLElement>(null);
  const closeCallbackRef = useRef(close);

  useEffect(() => {
    closeCallbackRef.current = close;
  }, [close]);

  useEffect(() => {
    const previousFocus = document.activeElement instanceof HTMLElement ? document.activeElement : null;
    const element = modalRef.current;
    if (!element) return;
    if (modalStack.length === 0) {
      previousBodyOverflow = document.body.style.overflow;
      document.body.style.overflow = "hidden";
    }
    const entry: ModalEntry = {
      element,
      close: () => closeCallbackRef.current(),
      previousFocus,
    };
    modalStack.push(entry);
    closeRef.current?.focus();
    const onKeyDown = (event: KeyboardEvent) => {
      if (modalStack.at(-1) !== entry) return;
      if (event.key === "Escape") {
        event.preventDefault();
        entry.close();
        return;
      }
      if (event.key !== "Tab") return;
      const focusable = focusableElements(element);
      if (!focusable.length) {
        event.preventDefault();
        element.focus();
        return;
      }
      const first = focusable[0];
      const last = focusable[focusable.length - 1];
      if (event.shiftKey && (document.activeElement === first || !element.contains(document.activeElement))) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && (document.activeElement === last || !element.contains(document.activeElement))) {
        event.preventDefault();
        first.focus();
      }
    };
    document.addEventListener("keydown", onKeyDown);
    return () => {
      document.removeEventListener("keydown", onKeyDown);
      const wasTopModal = modalStack.at(-1) === entry;
      const index = modalStack.indexOf(entry);
      if (index !== -1) modalStack.splice(index, 1);
      if (modalStack.length === 0) {
        document.body.style.overflow = previousBodyOverflow;
      }
      if (wasTopModal && previousFocus?.isConnected) previousFocus.focus();
    };
  }, []);

  return (
    <div
      className="modal-backdrop"
      onMouseDown={(e) => e.target === e.currentTarget && modalStack.at(-1)?.element === modalRef.current && closeCallbackRef.current()}
    >
      <section ref={modalRef} className="modal" role="dialog" tabIndex={-1} aria-modal="true" aria-labelledby={titleId}>
        <header>
          <h2 id={titleId}>{title}</h2>
          <button ref={closeRef} aria-label="Close" onClick={close}>
            <X size={18} />
          </button>
        </header>
        {children}
      </section>
    </div>
  );
}
