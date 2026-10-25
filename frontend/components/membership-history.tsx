"use client";

import type { Row } from "@/lib/api";
import { NbButton } from "@/components/nb/button";
import { NbState } from "@/components/nb/state";
import type { ViewState } from "@/lib/data-state";

type MembershipHistoryProps = {
  members: readonly Row[];
  loading: boolean;
  error: string;
  retry: () => void;
  canManage: boolean;
  busy: boolean;
  onEnd: (id: string) => void;
};

export function MembershipHistory({
  members,
  loading,
  error,
  retry,
  canManage,
  busy,
  onEnd,
}: MembershipHistoryProps) {
  const rows = members;
  let state: ViewState<readonly Row[]>;

  if (loading) {
    state = { status: "loading" };
  } else if (error && rows.length === 0) {
    state = { status: "error", error: { message: error, retryable: true }, retry };
  } else if (error) {
    state = {
      status: "partial",
      data: rows,
      filter: { label: "Try again", clear: retry },
      totalCount: rows.length,
    };
  } else if (rows.length === 0) {
    state = { status: "empty", reason: "no-data" };
  } else {
    state = { status: "populated", data: rows };
  }

  return (
    <NbState
      state={state}
      empty="No membership history returned."
      className="membership-list"
      loadingLabel="Loading membership history"
      sourceMessage={error || undefined}
      partialSummary="Some membership history could not be loaded."
      partialActionLabel="Try again"
      partialActionAriaLabel="Try again to load membership history"
      nextAction={<NbButton variant="secondary" onClick={retry}>Try again</NbButton>}
    >
      {(data) => (
        <>
          {data.map((member) => (
            <div className="membership-line" key={String(member.id)}>
              <div>
                <b>{String(member.team_name || member.driver_name || "Membership")}</b>
                <small>{String(member.start_date || "")} → {String(member.end_date || "Current")}</small>
              </div>
              {canManage && !member.end_date && (
                <NbButton
                  variant="secondary"
                  disabled={busy}
                  onClick={() => onEnd(String(member.id))}
                >
                  End membership
                </NbButton>
              )}
            </div>
          ))}
        </>
      )}
    </NbState>
  );
}
