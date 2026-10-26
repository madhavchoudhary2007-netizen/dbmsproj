"use client";

import { useId, useRef, useState } from "react";
import { Row } from "@/lib/api";
import { NbField } from "@/components/nb/field";
import { NbButton } from "@/components/nb/button";
import { NbInput, NbSelect } from "@/components/nb/input";
import { useFieldValidation } from "@/lib/use-field-validation";

export type FieldOption = string | { value: string; label: string };

export type ResourceEditorField = {
  name: string;
  label?: string;
  type?: string;
  required?: boolean;
  min?: number;
  max?: number;
  options?: FieldOption[];
};

export type ResourceEditorProps = {
  fields: ResourceEditorField[];
  initial?: Row;
  save: (row: Row) => Promise<void>;
  busy: boolean;
  primary?: boolean;
};

export function ResourceEditor({
  fields,
  initial,
  save,
  busy,
  primary = false,
}: ResourceEditorProps) {
  const [vals, setVals] = useState<Row>(initial || {});
  const [err, setErr] = useState("");
  const { errors, validate, revalidate } = useFieldValidation();
  const saveInFlight = useRef(false);
  const formId = useId();

  return (
    <form
      className="form-grid"
      onSubmit={async (e) => {
        e.preventDefault();
        if (saveInFlight.current) return;
        saveInFlight.current = true;
        setErr("");
        try {
          const payload = { ...vals };
          fields
            .filter((f) => f.type === "datetime-local")
            .forEach((f) => {
              const v = payload[f.name];
              if (typeof v === "string" && v)
                payload[f.name] = new Date(v).toISOString();
            });
          await save(payload);
        } catch (ex) {
          setErr(ex instanceof Error ? ex.message : "Save failed");
        } finally {
          saveInFlight.current = false;
        }
      }}
    >
      {fields.map((f) => (
        <NbField key={f.name} id={`${formId}-${f.name}`} label={f.label || f.name.replaceAll("_", " ")} error={errors[f.name]}>
          {f.options ? (
            <NbSelect
              required={f.required}
              value={
                f.type === "datetime-local" && vals[f.name]
                  ? new Date(String(vals[f.name]))
                      .toLocaleString("sv-SE")
                      .replace(" ", "T")
                      .slice(0, 16)
                  : String(vals[f.name] ?? "")
              }
              onBlur={(e) => validate(f.name, e.currentTarget)}
              onInvalid={(e) => validate(f.name, e.currentTarget)}
              onChange={(e) => {
                revalidate(f.name, e.currentTarget);
                setVals({ ...vals, [f.name]: e.target.value });
              }}
            >
              <option value="">Select…</option>
              {f.options.map((x) => {
                const value = typeof x === "string" ? x : x.value;
                const label = typeof x === "string" ? x : x.label;
                return (
                  <option key={value} value={value}>
                    {label}
                  </option>
                );
              })}
            </NbSelect>
          ) : (
            <NbInput
              required={f.required}
              type={f.type || "text"}
              min={f.min}
              max={f.max}
              value={
                f.type === "datetime-local" && vals[f.name]
                  ? new Date(String(vals[f.name]))
                      .toLocaleString("sv-SE")
                      .replace(" ", "T")
                      .slice(0, 16)
                  : String(vals[f.name] ?? "")
              }
              onBlur={(e) => validate(f.name, e.currentTarget)}
              onInvalid={(e) => validate(f.name, e.currentTarget)}
              onChange={(e) => {
                revalidate(f.name, e.currentTarget);
                setVals({
                  ...vals,
                  [f.name]:
                    f.type === "number"
                      ? e.target.value === "" ? undefined : Number(e.target.value)
                      : e.target.value,
                });
              }}
            />
          )}
        </NbField>
      ))}
      {err && <div className="form-error" role="alert">{err}</div>}
      <div className="form-actions">
        <NbButton type="submit" variant="primary" data-primary={primary || undefined} disabled={busy}>
          {busy ? "Saving…" : "Save record"}
        </NbButton>
      </div>
    </form>
  );
}
