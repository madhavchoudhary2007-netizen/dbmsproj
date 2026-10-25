"use client";

import { useState } from "react";

export type ValidatableField = Pick<
  HTMLInputElement,
  "validity" | "validationMessage"
>;

export function useFieldValidation(): {
  errors: Record<string, string>;
  validate: (name: string, field: ValidatableField) => void;
  revalidate: (name: string, field: ValidatableField) => void;
} {
  const [errors, setErrors] = useState<Record<string, string>>({});

  const update = (name: string, field: ValidatableField, onlyIfInvalid: boolean) => {
    const invalid = !field.validity.valid;
    const message = field.validationMessage;
    setErrors((current) => {
      if (onlyIfInvalid && !(name in current)) return current;
      if (invalid) {
        if (current[name] === message) return current;
        return { ...current, [name]: message };
      }
      if (!(name in current)) return current;
      const next = { ...current };
      delete next[name];
      return next;
    });
  };

  return {
    errors,
    validate: (name, field) => update(name, field, false),
    revalidate: (name, field) => update(name, field, true),
  };
}
