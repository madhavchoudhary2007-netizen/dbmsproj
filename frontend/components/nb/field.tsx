"use client";

import * as React from "react";

import { cn } from "@/lib/cn";

type NbFieldControlProps = {
  id?: string;
  "aria-describedby"?: string;
  "aria-invalid"?: React.AriaAttributes["aria-invalid"];
};

export interface NbFieldProps {
  id: string;
  label: React.ReactNode;
  error?: string;
  description?: React.ReactNode;
  className?: string;
  children: React.ReactElement<NbFieldControlProps>;
}

export function NbField({
  id,
  label,
  error,
  description,
  className,
  children,
}: NbFieldProps) {
  const descriptionId = `${id}-description`;
  const errorId = `${id}-error`;
  const generatedIds = [description ? descriptionId : null, error ? errorId : null].filter(
    (value): value is string => Boolean(value),
  );
  const existingDescribedBy = children.props["aria-describedby"];
  const describedBy = [existingDescribedBy, ...generatedIds].filter(Boolean).join(" ");

  const control = React.cloneElement(children, {
    id,
    ...(generatedIds.length > 0 ? { "aria-describedby": describedBy } : {}),
    ...(error ? { "aria-invalid": true } : {}),
  });

  return (
    <div className={cn("flex w-full min-w-0 flex-col gap-2", className)}>
      <label htmlFor={id} className="font-sans text-[length:var(--fs-label)] font-medium text-ink">
        {label}
      </label>
      {control}
      {description ? (
        <p id={descriptionId} className="font-sans text-[length:var(--fs-label)] text-ink">
          {description}
        </p>
      ) : null}
      {error ? (
        <p
          id={errorId}
          role="alert"
          className="bg-red px-2 py-2 font-sans text-[length:var(--fs-label)] font-medium text-ink"
        >
          {error}
        </p>
      ) : null}
    </div>
  );
}
