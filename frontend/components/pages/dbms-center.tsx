"use client";

import { useAuth } from "../auth";
import { DbmsWorkspace } from "../dbms-workspace";
import { Button, PageHeader, StateMessage } from "../ui";

export function DbmsCenter() {
  const { user } = useAuth();
  if (user?.role !== "ADMIN") {
    return <>
      <PageHeader eyebrow="PLATFORM / DATABASE ENGINEERING" title="DBMS operations" description="Database diagnostics require an administrator account." />
      <StateMessage error="ADMIN role required to run database operations." />
    </>;
  }
  return <>
    <PageHeader eyebrow="PLATFORM / DATABASE ENGINEERING" title="DBMS workspace" description="Inspect live PostgreSQL and MongoDB records, explore the model, and run real database operations from one workspace." action={<Button data-primary="true" onClick={() => { if (typeof window !== "undefined") window.location.hash = "overview"; }}>Overview</Button>} />
    <DbmsWorkspace />
  </>;
}
