"use client";

import { useEffect, useRef, type RefObject } from "react";

export function useNativeDialog(
  dialogRef: RefObject<HTMLDialogElement | null>,
  open: boolean,
  onClose: () => void,
): void {
  const onCloseRef = useRef(onClose);
  const previousFocusRef = useRef<HTMLElement | null>(null);
  const suppressCloseRef = useRef(false);
  const didNotifyCloseRef = useRef(false);
  useEffect(() => { onCloseRef.current = onClose; }, [onClose]);
  useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog) return;
    const restoreFocus = () => {
      const previousFocus = previousFocusRef.current;
      previousFocusRef.current = null;
      if (previousFocus?.isConnected) previousFocus.focus();
    };
    const handleClose = () => {
      if (dialog.open) return;
      const suppressed = suppressCloseRef.current;
      suppressCloseRef.current = false;
      restoreFocus();
      if (suppressed || didNotifyCloseRef.current) return;
      didNotifyCloseRef.current = true;
      onCloseRef.current();
    };
    const handleClick = (event: MouseEvent) => {
      if (event.target !== dialog || !dialog.open) return;
      const rect = dialog.getBoundingClientRect();
      const outside = event.clientX < rect.left || event.clientX > rect.right || event.clientY < rect.top || event.clientY > rect.bottom;
      if (outside) dialog.close();
    };
    dialog.addEventListener("close", handleClose);
    dialog.addEventListener("click", handleClick);
    return () => {
      if (dialog.open) {
        suppressCloseRef.current = true;
        dialog.close();
      }
      dialog.removeEventListener("close", handleClose);
      dialog.removeEventListener("click", handleClick);
      restoreFocus();
    };
  }, [dialogRef]);
  useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog) return;
    if (open) {
      didNotifyCloseRef.current = false;
      suppressCloseRef.current = false;
      if (!dialog.open) {
        previousFocusRef.current = document.activeElement instanceof HTMLElement ? document.activeElement : null;
        dialog.showModal();
      }
      return;
    }
    if (dialog.open) {
      suppressCloseRef.current = true;
      dialog.close();
    }
  }, [dialogRef, open]);
}
