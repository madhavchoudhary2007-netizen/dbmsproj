"use client";

import { useCallback, useMemo, useState, type Dispatch, type SetStateAction } from "react";

export type NbDemoRow = Readonly<{ id: string; label: string }>;
const SMALL_ROWS: readonly NbDemoRow[] = [
  { id: "row-1", label: "First row" },
  { id: "row-2", label: "Second row" },
  { id: "row-3", label: "Third row" },
];
const LARGE_ROWS: readonly NbDemoRow[] = Array.from({ length: 32 }, (_, index) => ({
  id: `row-${index + 1}`,
  label: `Row ${index + 1}`,
}));
export function useNbDemo(): {
  tab: string;
  setTab: Dispatch<SetStateAction<string>>;
  modalOpen: boolean;
  openModal: () => void;
  closeModal: () => void;
  value: number;
  increment: () => void;
  rows: readonly NbDemoRow[];
  reverseRows: () => void;
  toggleLarge: () => void;
} {
  const [tab, setTab] = useState("overview");
  const [modalOpen, setModalOpen] = useState(false);
  const [value, setValue] = useState(0);
  const [large, setLarge] = useState(false);
  const [reversed, setReversed] = useState(false);
  const rows = useMemo(() => {
    const source = large ? LARGE_ROWS : SMALL_ROWS;
    return reversed ? [...source].reverse() : source;
  }, [large, reversed]);
  const openModal = useCallback(() => setModalOpen(true), []);
  const closeModal = useCallback(() => setModalOpen(false), []);
  const increment = useCallback(() => setValue((current) => current + 1), []);
  const reverseRows = useCallback(() => setReversed((current) => !current), []);
  const toggleLarge = useCallback(() => setLarge((current) => !current), []);
  return { tab, setTab, modalOpen, openModal, closeModal, value, increment, rows, reverseRows, toggleLarge };
}
