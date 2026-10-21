import { ResourcePage } from "@/components/resource-page";

export default function Page() {
  return (
    <ResourcePage
      eyebrow="PEOPLE & TEAMS / ACCESS"
      title="Users"
      description="Create and maintain operator, principal, steward, and driver accounts. Passwords are write-only."
      endpoint="/users"
      columns={["full_name", "email", "role"]}
      fields={[
        { name: "full_name", required: true },
        { name: "email", type: "email", required: true },
        { name: "password", type: "password", required: true },
        {
          name: "role",
          required: true,
          options: ["ADMIN", "STEWARD", "PRINCIPAL", "DRIVER"],
        },
      ]}
    />
  );
}
