"use client";

import type { Row } from "@/lib/api";
import { NbButton } from "./nb/button";
import { NbModal } from "./nb/modal";
import { Button, ResourceEditor } from "./ui";
import { MembershipHistory } from "./membership-history";

export type FieldOption = string | { value: string; label: string };

export type Field = {
  name: string;
  type?: string;
  required?: boolean;
  min?: number;
  max?: number;
  options?: FieldOption[];
};

const MEMBER_FIELDS: Field[] = [
  { name: "driver_id", required: true },
  { name: "team_id", required: true },
  { name: "start_date", type: "date", required: true },
  { name: "end_date", type: "date" },
];

export function buildMemberFormFields(entityRows: Record<string, Row[]>): Field[] {
  return MEMBER_FIELDS.map((field) => ({
    ...field,
    options: (entityRows[field.name] || []).map((row) => ({
      value: String(row.id),
      label:
        field.name === "driver_id"
          ? `${String(row.number || "#—")} · ${String(row.full_name || "Driver")}`
          : `${String(row.name || "Team")} · ${String(row.principal_name || "")}`,
    })),
  }));
}

export interface ResourceRecordModalProps {
  open: boolean;
  edit?: Row;
  canManage: boolean;
  columns: string[];
  formFields: Field[];
  userField?: string;
  userRole?: string;
  userLoadError: string;
  userOptions: { value: string; label: string }[];
  endpoint: string;
  busy: boolean;
  primary: boolean;
  actionError: string;
  supportsHistory: boolean;
  members: readonly Row[];
  membersLoading: boolean;
  memberError: string;
  retryMembers: () => void;
  endMembership: (id: string) => Promise<void>;
  onSave: (v: Row) => Promise<void>;
  onDelete: () => void;
  onAddMembership: () => void;
  onClose: () => void;
}

export function ResourceRecordModal({
  open, edit, canManage, columns, formFields, userField, userRole,
  userLoadError, userOptions, endpoint, busy, primary, actionError,
  supportsHistory, members, membersLoading, memberError, retryMembers,
  endMembership, onSave, onDelete, onAddMembership, onClose,
}: ResourceRecordModalProps) {
  if (!open) return null;

  return (
    <NbModal open={open} title={edit ? "Record details" : "Create record"} onClose={onClose}>
      {canManage ? (
        <>
          {userField && userLoadError && (
            <div className="form-error">Could not load selectable accounts: {userLoadError}</div>
          )}
          {userField && !userLoadError && userOptions.length === 0 && (
            <div className="form-hint">
              No matching accounts are available. Create a {userRole || "user"} account on the Users page first.
            </div>
          )}
          {endpoint === "/users" && edit?.id && (
            <div className="form-hint">
              Leave password blank to keep the existing password. Passwords are write-only.
            </div>
          )}
          <ResourceEditor fields={formFields} initial={edit} save={onSave} busy={busy} primary={primary} />
        </>
      ) : (
        <div className="read-detail">
          {columns.map((k) => (
            <div className="detail-row" key={k}>
              <span>{k.replaceAll("_", " ")}</span>
              <b>{String(edit?.[k] ?? "—")}</b>
            </div>
          ))}
        </div>
      )}
      {actionError && <div className="form-error">{actionError}</div>}
      {canManage && edit && (
        <div className="form-actions destructive-row">
          <Button kind="danger" disabled={busy} onClick={onDelete}>Delete record</Button>
        </div>
      )}
      {supportsHistory && edit && (
        <div className="membership-history">
          <div className="panel-heading">
            <div>
              <div className="eyebrow">TEAM MEMBERSHIP HISTORY</div>
              <h2>{String(edit.full_name || edit.name || "Selected record")}</h2>
            </div>
            {canManage && (
              <Button kind="secondary" onClick={onAddMembership}>Add membership</Button>
            )}
          </div>
          <MembershipHistory
            members={members}
            loading={membersLoading}
            error={memberError}
            retry={retryMembers}
            canManage={canManage}
            busy={busy}
            onEnd={(id) => void endMembership(id)}
          />
        </div>
      )}
    </NbModal>
  );
}

export interface ResourceDeleteModalProps {
  open: boolean;
  edit?: Row;
  busy: boolean;
  onCancel: () => void;
  onConfirm: () => void;
}

export function ResourceDeleteModal({
  open, edit, busy, onCancel, onConfirm,
}: ResourceDeleteModalProps) {
  if (!open || !edit) return null;

  return (
    <NbModal open={open} title="Delete record" onClose={onCancel}>
      <p className="min-w-0 [overflow-wrap:anywhere]">
        Delete {String(edit.full_name || edit.name || edit.id)}? This action cannot be undone.
      </p>
      <div className="form-actions">
        <NbButton variant="secondary" disabled={busy} onClick={onCancel}>Cancel</NbButton>
        <NbButton
          variant="danger"
          data-primary={open ? "true" : undefined}
          disabled={busy}
          onClick={onConfirm}
        >
          Delete record
        </NbButton>
      </div>
    </NbModal>
  );
}

export interface ResourceMembershipModalProps {
  open: boolean;
  edit?: Row;
  supportsHistory: boolean;
  currentMembers: readonly Row[];
  membersLoading: boolean;
  memberError: string;
  retryMembers: () => void;
  busy: boolean;
  deleteConfirm: boolean;
  entityRows: Record<string, Row[]>;
  onSave: (v: Row) => Promise<void>;
  onEndMembership: (id: string) => Promise<void>;
  onClose: () => void;
}

export function ResourceMembershipModal({
  open, edit, supportsHistory, currentMembers, membersLoading, memberError,
  retryMembers, busy, deleteConfirm, entityRows, onSave, onEndMembership, onClose,
}: ResourceMembershipModalProps) {
  if (!open) return null;

  const memberFormFields = buildMemberFormFields(entityRows);

  return (
    <NbModal open={open} title="Create team membership" onClose={onClose}>
      <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
        <section className="min-w-0">
          <h3 className="mb-4 text-lg font-bold">Current roster</h3>
          {edit && supportsHistory ? (
            <>
              <p className="mb-4">{String(edit.full_name || edit.name || "Selected record")}</p>
              <MembershipHistory
                members={currentMembers}
                loading={membersLoading}
                error={memberError}
                retry={retryMembers}
                canManage={false}
                busy={busy}
                onEnd={(id) => void onEndMembership(id)}
              />
            </>
          ) : (
            <p>Select a driver or team record to inspect its roster.</p>
          )}
        </section>
        <section className="min-w-0">
          <h3 className="mb-4 text-lg font-bold">Add membership</h3>
          <div className="form-hint">
            Choose the driver, team, and dates. The membership appears in both history views.
          </div>
          {memberError && <div className="form-error">{memberError}</div>}
          <ResourceEditor fields={memberFormFields} save={onSave} busy={busy} primary={!deleteConfirm} />
        </section>
      </div>
    </NbModal>
  );
}

export interface ResourceModalsProps {
  record: ResourceRecordModalProps;
  deleteDialog: ResourceDeleteModalProps;
  membership: ResourceMembershipModalProps;
}

export function ResourceModals({
  record,
  deleteDialog,
  membership,
}: ResourceModalsProps) {
  return (
    <>
      <ResourceRecordModal {...record} />
      <ResourceDeleteModal {...deleteDialog} />
      <ResourceMembershipModal {...membership} />
    </>
  );
}
