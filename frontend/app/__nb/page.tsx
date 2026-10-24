import { notFound } from "next/navigation";

import { NbStyleGuide } from "@/components/nb/style-guide";

export default function NbPage() {
  if (process.env.NODE_ENV === "production") notFound();
  return <NbStyleGuide />;
}
