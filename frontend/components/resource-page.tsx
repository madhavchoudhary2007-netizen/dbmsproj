"use client";
import { useCallback, useEffect, useMemo, useState } from "react";
import { api, asArray, listAll, Row } from "@/lib/api";
import { useAuth } from "./auth";
import {
  AddButton,
  Button,
  DataTable,
  Modal,
  PageHeader,
  ReloadButton,
  ResourceEditor,
  SearchBox,
  StateMessage,
} from "./ui";

type FieldOption = string | { value: string; label: string };
type Field = {
  name: string;
  type?: string;
  required?: boolean;
  min?: number;
  max?: number;
  options?: FieldOption[];
};
export function ResourcePage({
  title,
  eyebrow,
  description,
  endpoint,
  columns,
  fields,
  userField,
  userRole,
}: {
  title: string;
  eyebrow: string;
  description: string;
  endpoint: string;
  columns: string[];
  fields: Field[];
  userField?: string;
  userRole?: string;
}) {
  const [rows, setRows] = useState<Row[]>([]),
    [loading, setLoading] = useState(true),
    [error, setError] = useState(""),
    [term, setTerm] = useState(""),
    [page, setPage] = useState(0),
    [modal, setModal] = useState(false),
    [edit, setEdit] = useState<Row | undefined>(),
    [busy, setBusy] = useState(false),
    [members, setMembers] = useState<Row[]>([]),
    [memberError, setMemberError] = useState(""),
    [memberModal, setMemberModal] = useState(false),
    [users, setUsers] = useState<Row[]>([]),
    [relatedRows, setRelatedRows] = useState<Record<string, Row[]>>({}),
    [entityRows, setEntityRows] = useState<Record<string, Row[]>>({}),
    [userLoadError, setUserLoadError] = useState(""),
    [actionError, setActionError] = useState("");
  const supportsHistory = endpoint === "/drivers" || endpoint === "/teams";
  const { user } = useAuth();
  const canManage = user?.role === "ADMIN";
  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      setRows(await listAll(endpoint));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unable to load records");
    } finally {
      setLoading(false);
    }
  }, [endpoint]);
  useEffect(() => {
    void load();
  }, [load]);
  useEffect(() => {
    if (!userField || !canManage) return;
    listAll("/users")
      .then((rows) => {
        setUsers(asArray(rows));
        setUserLoadError("");
      })
      .catch((e) =>
        setUserLoadError(
          e instanceof Error ? e.message : "Unable to load user accounts",
        ),
      );
  }, [canManage, userField]);
  useEffect(() => {
    if (!canManage || endpoint !== "/events") return;
    Promise.all([listAll("/championships"), listAll("/circuits")])
      .then(([championships, circuits]) =>
        setRelatedRows({
          championship_id: asArray(championships),
          circuit_id: asArray(circuits),
        }),
      )
      .catch((e) =>
        setActionError(
          e instanceof Error ? e.message : "Unable to load event choices",
        ),
      );
  }, [canManage, endpoint]);
  useEffect(() => {
    if (!supportsHistory || !canManage) return;
    Promise.all([listAll("/drivers"), listAll("/teams")])
      .then(([drivers, teams]) =>
        setEntityRows({
          driver_id: asArray(drivers),
          team_id: asArray(teams),
        }),
      )
      .catch((e) =>
        setMemberError(
          e instanceof Error ? e.message : "Unable to load membership choices",
        ),
      );
  }, [canManage, supportsHistory]);
  const userOptions = users
    .filter((row) => !userRole || row.role === userRole)
    .filter((row) => endpoint !== "/drivers" || edit?.user_id === row.id || !rows.some((driver) => driver.user_id === row.id))
    .map((row) => ({
      value: String(row.id),
      label: `${String(row.full_name || "Unnamed account")} · ${String(row.email || "")}`,
    }));
  const formFields = fields.map((field) => {
    if (field.name === userField) return { ...field, options: userOptions };
    if (relatedRows[field.name])
      return {
        ...field,
        options: relatedRows[field.name].map((row) => ({
          value: String(row.id),
          label: String(row.name || row.id),
        })),
      };
    if (endpoint === "/users" && field.name === "password")
      return { ...field, required: !edit?.id };
    return field;
  });
  const filtered = useMemo(
    () =>
      rows.filter((r) =>
        JSON.stringify(r).toLowerCase().includes(term.toLowerCase()),
      ),
    [rows, term],
  );
  const pageSize = 50;
  const pageCount = Math.max(1, Math.ceil(filtered.length / pageSize));
  const visiblePage = Math.min(page, pageCount - 1);
  const visibleRows = filtered.slice(visiblePage * pageSize, (visiblePage + 1) * pageSize);
  const save = async (v: Row) => {
    setBusy(true);
    try {
      const payload = Object.fromEntries(
        fields
          .map(({ name }) => [name, v[name]])
          .filter(([, value]) => value !== undefined),
      ) as Row;
      if (endpoint === "/users" && edit?.id && !payload.password)
        delete payload.password;
      if (edit?.id)
        await api(`${endpoint}/${edit.id}`, {
          method: "PATCH",
          body: JSON.stringify(payload),
        });
      else
        await api(endpoint, { method: "POST", body: JSON.stringify(payload) });
      setModal(false);
      setActionError("");
      await load();
    } catch (e) {
      setActionError(e instanceof Error ? e.message : "Unable to save record");
      throw e;
    } finally {
      setBusy(false);
    }
  };
  const remove = async () => {
    if (!edit?.id) return;
    setBusy(true);
    try {
      await api(`${endpoint}/${edit.id}`, { method: "DELETE" });
      setModal(false);
      setEdit(undefined);
      await load();
    } catch (e) {
      setActionError(
        e instanceof Error ? e.message : "Unable to delete record",
      );
    } finally {
      setBusy(false);
    }
  };
  const showRow = async (row: Row) => {
    setEdit(row);
    setActionError("");
    setModal(true);
    setMembers([]);
    setMemberError("");
    if (supportsHistory && row.id) {
      try {
        setMembers(
          asArray(await api(`/${endpoint.slice(1)}/${row.id}/memberships`)),
        );
      } catch (e) {
        setMemberError(
          e instanceof Error ? e.message : "Unable to load membership history",
        );
      }
    }
  };
  const memberSave = async (v: Row) => {
    setBusy(true);
    try {
      await api("/team-memberships", {
        method: "POST",
        body: JSON.stringify(v),
      });
      setMemberModal(false);
      if (edit?.id && supportsHistory)
        setMembers(
          asArray(await api(`/${endpoint.slice(1)}/${edit.id}/memberships`)),
        );
      await load();
    } finally {
      setBusy(false);
    }
  };
  const endMembership = async (id: string) => {
    if (!edit?.id) return;
    setBusy(true);
    try {
      await api(`/team-memberships/${id}`, {
        method: "PATCH",
        body: JSON.stringify({
          end_date: new Date().toISOString().slice(0, 10),
        }),
      });
      setMembers(
        asArray(await api(`/${endpoint.slice(1)}/${edit.id}/memberships`)),
      );
    } catch (e) {
      setMemberError(
        e instanceof Error ? e.message : "Unable to update membership",
      );
    } finally {
      setBusy(false);
    }
  };
  const memberFields: Field[] = [
    { name: "driver_id", required: true },
    { name: "team_id", required: true },
    { name: "start_date", type: "date", required: true },
    { name: "end_date", type: "date" },
  ];
  const memberFormFields = memberFields.map((field) => ({
    ...field,
    options: (entityRows[field.name] || []).map((row) => ({
      value: String(row.id),
      label:
        field.name === "driver_id"
          ? `${String(row.number || "#—")} · ${String(row.full_name || "Driver")}`
          : `${String(row.name || "Team")} · ${String(row.principal_name || "")}`,
    })),
  }));
  return (
    <>
      <PageHeader
        eyebrow={eyebrow}
        title={title}
        description={description}
        action={
          <div className="header-actions">
            {supportsHistory && canManage && (
              <Button
                kind="secondary"
                onClick={() => {
                  setEdit(undefined);
                  setMemberModal(true);
                }}
              >
                Add membership
              </Button>
            )}
            {canManage && (
              <AddButton
                onClick={() => {
                  setEdit(undefined);
                  setActionError("");
                  setModal(true);
                }}
              />
            )}
          </div>
        }
      />
      <div className="toolbar">
        <SearchBox value={term} onChange={(value) => { setTerm(value); setPage(0); }} />
        <span className="record-count">
          {loading
            ? "—"
            : `${filtered.length} RECORD${filtered.length === 1 ? "" : "S"}`}
        </span>
        <ReloadButton onClick={() => void load()} />
      </div>
      {error || loading ? (
        <StateMessage
          error={error}
          loading={loading}
          retry={() => void load()}
        />
      ) : filtered.length ? (
        <DataTable
          rows={visibleRows}
          columns={columns}
          onSelect={(row) => {
            if (canManage || supportsHistory) void showRow(row);
          }}
        />
      ) : (
        <StateMessage
          empty={
            term
              ? "No records match this filter."
              : "No records returned by the API."
          }
        />
      )}
      {!loading && !error && filtered.length > pageSize && (
        <div className="dbms-pagination resource-pagination">
          <span className="muted">Showing {visiblePage * pageSize + 1}–{Math.min((visiblePage + 1) * pageSize, filtered.length)} of {filtered.length}</span>
          <Button kind="secondary" disabled={visiblePage === 0} onClick={() => setPage((value) => Math.max(0, value - 1))}>Previous</Button>
          <span className="muted">Page {visiblePage + 1} of {pageCount}</span>
          <Button kind="secondary" disabled={visiblePage >= pageCount - 1} onClick={() => setPage((value) => value + 1)}>Next</Button>
        </div>
      )}
      <p className="table-note">
        Select a row to inspect or edit. Data is loaded from{" "}
        <code>/api{endpoint}</code>.
      </p>
      {modal && (
        <Modal
          title={edit ? "Record details" : "Create record"}
          close={() => setModal(false)}
        >
          {canManage ? (
            <>
              {userField && userLoadError && (
                <div className="form-error">
                  Could not load selectable accounts: {userLoadError}
                </div>
              )}
              {userField && !userLoadError && userOptions.length === 0 && (
                <div className="form-hint">
                  No matching accounts are available. Create a{" "}
                  {userRole || "user"} account on the Users page first.
                </div>
              )}
              {endpoint === "/users" && edit?.id && (
                <div className="form-hint">
                  Leave password blank to keep the existing password. Passwords
                  are write-only.
                </div>
              )}
              <ResourceEditor
                fields={formFields}
                initial={edit}
                save={save}
                busy={busy}
              />
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
              <Button
                kind="danger"
                disabled={busy}
                onClick={() => void remove()}
              >
                Delete record
              </Button>
            </div>
          )}
          {supportsHistory && edit && (
            <div className="membership-history">
              <div className="panel-heading">
                <div>
                  <div className="eyebrow">TEAM MEMBERSHIP HISTORY</div>
                  <h2>
                    {String(edit.full_name || edit.name || "Selected record")}
                  </h2>
                </div>
                {canManage && (
                  <Button kind="secondary" onClick={() => setMemberModal(true)}>
                    Add membership
                  </Button>
                )}
              </div>
              {memberError ? (
                <StateMessage error={memberError} />
              ) : (
                <div className="membership-list">
                  {members.map((m) => (
                    <div className="membership-line" key={String(m.id)}>
                      <div>
                        <b>
                          {String(m.team_name || m.driver_name || "Membership")}
                        </b>
                        <small>
                          {String(m.start_date || "")} →{" "}
                          {String(m.end_date || "Current")}
                        </small>
                      </div>
                      {canManage && !m.end_date && (
                        <Button
                          kind="secondary"
                          disabled={busy}
                          onClick={() => void endMembership(String(m.id))}
                        >
                          End membership
                        </Button>
                      )}
                    </div>
                  ))}
                  {members.length === 0 && (
                    <div className="state">No membership history returned.</div>
                  )}
                </div>
              )}
            </div>
          )}
        </Modal>
      )}
      {memberModal && canManage && (
        <Modal
          title="Create team membership"
          close={() => setMemberModal(false)}
        >
          <div className="form-hint">
            Choose the driver, team, and dates. The membership appears in both
            history views.
          </div>
          {memberError && <div className="form-error">{memberError}</div>}
          <ResourceEditor
            fields={memberFormFields}
            save={memberSave}
            busy={busy}
          />
        </Modal>
      )}
    </>
  );
}
