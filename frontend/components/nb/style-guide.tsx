"use client";
import { useRef } from "react";
import { NbBadge } from "./badge";
import { NbButton } from "./button";
import { NbCard } from "./card";
import { NbChartTooltip } from "./chart-frame";
import { NbField } from "./field";
import { NbInput, NbSelect, NbTextarea } from "./input";
import { NbMarquee } from "./marquee";
import { NbModal } from "./modal";
import { Arrow, CheckerStrip, RaceFlag, SpeedLines, StarBurst } from "./motifs";
import { NbSkeleton } from "./skeleton";
import { NbStat } from "./stat";
import { NbSticker } from "./sticker";
import { NbStyleGuideStates } from "./style-guide-states";
import { NbTabs } from "./tabs";
import { TyreBadge } from "./tyre-badge";
import { useFlashOnChange } from "@/lib/use-flash-on-change";
import { useFlip } from "@/lib/use-flip";
import { useNbDemo } from "@/lib/use-nb-demo";
const buttonVariants = ["primary", "secondary", "accent", "danger", "ghost"] as const;
const cardTones = ["paper", "cream", "yellow", "violet", "mint", "red"] as const;
const stickerTilts = [-3, -2, 2, 3] as const;
const cardShadows = [4, 8, 12] as const;
const statuses = ["SCHEDULED", "LIVE", "PAUSED", "FINISHED", "ARCHIVED", "OPEN", "APPROVED", "REJECTED", "RESERVED", "ACTIVE", "COMPLETED", "CANCELLED"] as const;
const compounds = ["SOFT", "MEDIUM", "HARD", "INTERMEDIATE", "WET"] as const;
const marqueeTones = ["red", "yellow", "paper"] as const;
const headingStyle = { fontSize: "var(--fs-h2)" };
export function NbStyleGuide() {
  const demo = useNbDemo();
  const rowsRef = useRef<HTMLUListElement>(null);
  const cellRef = useRef<HTMLSpanElement>(null);
  useFlip(rowsRef, demo.rows.map((row) => row.id));
  useFlashOnChange(cellRef, demo.value);

  return (
    <div data-testid="nb-guide" className="min-w-0 bg-cream p-4 text-ink">
      <h1 className="mb-8 font-bold" style={{ fontSize: "var(--fs-h1)" }}>ApexGrid component guide</h1>
      <section className="mb-8 min-w-0"><h2 className="mb-4 font-bold" style={headingStyle}>Buttons</h2>
        <div className="flex min-w-0 flex-wrap gap-4">
          {buttonVariants.map((variant) => (
            <NbButton
              key={variant}
              variant={variant}
              data-primary={variant === "primary" ? true : undefined}
              onClick={variant === "primary" ? demo.increment : undefined}
            >
              {variant === "primary" ? "Update example" : variant}
            </NbButton>
          ))}
          <NbButton size="lg" variant="secondary">Large button</NbButton>
          <NbButton busy variant="secondary">Busy button</NbButton>
          <NbButton disabled variant="secondary">Disabled button</NbButton>
        </div>
      </section>
      <section className="mb-8 min-w-0"><h2 className="mb-4 font-bold" style={headingStyle}>Cards</h2>
        <div className="grid min-w-0 grid-cols-1 gap-6 min-[1200px]:grid-cols-3">
          {cardTones.map((tone, index) => (
            <NbCard key={tone} tone={tone} shadow={cardShadows[index % cardShadows.length]}>
              Tone {tone}
            </NbCard>
          ))}
          <NbCard tone="yellow" shadow={8} interactive>
            <button type="button" className="min-h-11 min-w-11 border-4 border-ink bg-paper px-4 py-2 font-bold" onClick={demo.increment}>
              Native interactive button
            </button>
          </NbCard>
        </div>
      </section>
      <section className="mb-8 min-w-0"><h2 className="mb-4 font-bold" style={headingStyle}>Stickers and status</h2>
        <div className="flex min-w-0 flex-wrap gap-4">
          {cardTones.map((tone, index) => (
            <NbSticker key={tone} tone={tone} tilt={stickerTilts[index % stickerTilts.length]}>
              Sticker {tone}
            </NbSticker>
          ))}
          {statuses.map((status) => <NbBadge key={status} status={status} />)}
        </div>
      </section>
      <section className="mb-8 min-w-0"><h2 className="mb-4 font-bold" style={headingStyle}>Race primitives</h2>
        <div className="flex min-w-0 flex-wrap items-center gap-4">
          {compounds.map((compound) => <TyreBadge key={compound} compound={compound} />)}
          <StarBurst points={8} className="size-8" /><StarBurst points={12} className="size-8" />
          <Arrow direction="right" className="size-8" /><Arrow direction="diagonal" className="size-8" />
          {(["green", "yellow", "red", "chequered"] as const).map((tone) => <RaceFlag key={tone} tone={tone} className="size-12" />)}
          <CheckerStrip className="size-12" /><SpeedLines className="size-12" />
        </div>
      </section>
      <section className="mb-8 min-w-0"><h2 className="mb-4 font-bold" style={headingStyle}>Marquees and stats</h2>
        <div className="grid min-w-0 grid-cols-1 gap-6 min-[1200px]:grid-cols-3">
          {marqueeTones.map((tone) => <NbMarquee key={tone} tone={tone} items={[`${tone} feed one`, `${tone} feed two`]} />)}
          <NbStat value="42" label="Lap pace" delta="+3.2s" direction="up" />
          <NbStat value="18" label="Pit stops" delta="-1.0s" direction="down" />
          <NbStat value="7" label="Track temp" delta="0.0s" direction="flat" />
        </div>
      </section>
      <section className="mb-8 min-w-0"><h2 className="mb-4 font-bold" style={headingStyle}>Inputs</h2>
        <div className="grid min-w-0 grid-cols-1 gap-6 min-[1200px]:grid-cols-2">
          <NbField id="driver-name" label="Driver name"><NbInput autoComplete="name" /></NbField>
          <NbField id="error-field" label="Error field" error="Fixture validation error"><NbInput /></NbField>
          <NbField id="disabled-input" label="Disabled input"><NbInput disabled value="Locked fixture" readOnly /></NbField>
          <NbField id="compound" label="Compound"><NbSelect defaultValue="SOFT"><option value="SOFT">Soft</option><option value="MEDIUM">Medium</option></NbSelect></NbField>
          <NbField id="notes" label="Notes"><NbTextarea /></NbField>
        </div>
      </section>
      <section className="mb-8 min-w-0"><h2 className="mb-4 font-bold" style={headingStyle}>Skeletons and chart tooltip</h2>
        <div className="grid min-w-0 grid-cols-1 gap-6 min-[1200px]:grid-cols-3"><NbSkeleton variant="rows" /><NbSkeleton variant="card" /><NbSkeleton variant="chart" /></div>
        <div className="mt-6 flex min-w-0 flex-wrap gap-6"><NbChartTooltip active label="Fixture lap" payload={[{ name: "Nova Vale", value: 42 }]} /><NbChartTooltip active={false} label="Hidden fixture" payload={[]} /></div>
      </section>
      <section className="mb-8 min-w-0"><h2 className="mb-4 font-bold" style={headingStyle}>Tabs and modal</h2>
        <NbTabs
          id="guide-tabs"
          label="Fixture tabs"
          items={[
            { id: "overview", label: "Overview", panelId: "guide-panel-overview" },
            { id: "timing", label: "Timing", panelId: "guide-panel-timing" },
            { id: "disabled", label: "Disabled", disabled: true },
          ]}
          value={demo.tab}
          onChange={demo.setTab}
        />
        <section role="tabpanel" id="guide-panel-overview" aria-labelledby="guide-tabs-tab-overview" hidden={demo.tab !== "overview"} className="min-w-0 border-4 border-ink bg-paper p-4">Overview fixture panel</section>
        <section role="tabpanel" id="guide-panel-timing" aria-labelledby="guide-tabs-tab-timing" hidden={demo.tab !== "timing"} className="min-w-0 border-4 border-ink bg-paper p-4">Timing fixture panel</section>
        <div className="mt-4"><NbButton onClick={demo.openModal}>Open modal</NbButton></div>
        <NbModal open={demo.modalOpen} title="Fixture modal" onClose={() => { demo.closeModal(); demo.increment(); }}>
          <NbField id="modal-notes" label="Modal notes"><NbInput /></NbField>
        </NbModal>
      </section>
      <section className="mb-8 min-w-0"><h2 className="mb-4 font-bold" style={headingStyle}>Motion fixtures</h2>
        <div className="flex min-w-0 flex-wrap gap-4">
          <NbButton onClick={demo.reverseRows}>Reverse rows</NbButton>
          <NbButton onClick={demo.toggleLarge}>Toggle large list</NbButton>
          <span ref={cellRef} data-testid="demo-value" className="min-h-12 border-4 border-ink bg-paper px-4 py-3 font-mono">Value {demo.value}</span>
        </div>
        <ul ref={rowsRef} data-testid="flip-rows" className="mt-6 min-w-0">
          {demo.rows.map((row) => <li key={row.id} data-flip-key={row.id} className="min-h-12 border-b-4 border-ink py-3">{row.label}</li>)}
        </ul>
      </section>
      <NbStyleGuideStates onAction={demo.increment} />
    </div>
  );
}
