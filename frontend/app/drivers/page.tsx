import { ResourcePage } from "@/components/resource-page";
export default function Page() {
  return (
    <ResourcePage
      eyebrow="PEOPLE & TEAMS / COMPETITORS"
      title="Drivers"
      description="Manage driver licensing, race eligibility, and team membership history."
      endpoint="/drivers"
      columns={[
        "full_name",
        "number",
        "licence_number",
        "eligibility",
        "team_name",
      ]}
      userField="user_id"
      userRole="DRIVER"
      fields={[
        { name: "user_id", required: true },
        { name: "licence_number", required: true },
        { name: "number", type: "number", required: true, min: 1, max: 999 },
      ]}
    />
  );
}
