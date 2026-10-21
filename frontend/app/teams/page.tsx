import { ResourcePage } from "@/components/resource-page";
export default function Page() {
  return (
    <ResourcePage
      eyebrow="PEOPLE & TEAMS / COMPETITORS"
      title="Teams"
      description="Manage entrants, principal accounts, and current or historic driver membership."
      endpoint="/teams"
      columns={["name", "principal_name", "id"]}
      userField="principal_user_id"
      userRole="PRINCIPAL"
      fields={[
        { name: "name", required: true },
        { name: "principal_user_id", required: true },
      ]}
    />
  );
}
