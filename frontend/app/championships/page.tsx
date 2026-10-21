import { ResourcePage } from "@/components/resource-page";
export default function Page() {
  return (
    <ResourcePage
      eyebrow="CHAMPIONSHIP / PROGRAMME"
      title="Championships"
      description="Manage championship series and season configuration."
      endpoint="/championships"
      columns={["name", "season", "id"]}
      fields={[
        { name: "name", required: true },
        { name: "season", type: "number", required: true },
      ]}
    />
  );
}
