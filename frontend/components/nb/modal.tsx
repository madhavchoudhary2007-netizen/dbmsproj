"use client";

import {
  forwardRef,
  useId,
  useImperativeHandle,
  useRef,
  type ReactNode,
} from "react";
import { cn } from "@/lib/cn";
import { useNativeDialog } from "@/lib/use-native-dialog";

export type NbModalProps = {
  open: boolean;
  title: ReactNode;
  onClose: () => void;
  children: ReactNode;
  className?: string;
};

export const NbModal = forwardRef<HTMLDialogElement, NbModalProps>(
  function NbModal({ open, title, onClose, children, className }, ref) {
    const dialogRef = useRef<HTMLDialogElement>(null);
    const titleId = useId();

    useImperativeHandle(ref, () => dialogRef.current as HTMLDialogElement, []);
    useNativeDialog(dialogRef, open, onClose);

    return (
      <dialog
        ref={dialogRef}
        aria-labelledby={titleId}
        className={cn(
          "fixed inset-0 m-auto max-h-[calc(100dvh-32px)] w-[calc(100%-32px)] max-w-3xl min-w-0 overflow-y-auto border-4 border-ink bg-paper p-0 text-ink shadow-nb-12 backdrop:bg-cream/90 max-[619px]:shadow-nb-8",
          className,
        )}
      >
        <div className="min-w-0">
          <header className="flex items-center justify-between gap-4 border-b-4 border-ink bg-ink p-4 text-paper">
            <h2 id={titleId} className="min-w-0 text-xl font-bold">
              {title}
            </h2>
            <button
              type="button"
              aria-label="Close"
              className="nb-focus min-h-[44px] min-w-[44px] border-4 border-paper bg-ink text-2xl leading-none text-paper focus-visible:text-ink"
              onClick={onClose}
            >
              ×
            </button>
          </header>
          <div className="min-w-0 p-4">{children}</div>
        </div>
      </dialog>
    );
  },
);
