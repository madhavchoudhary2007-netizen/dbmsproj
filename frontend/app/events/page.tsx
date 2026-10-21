import { ResourcePage } from "@/components/resource-page";
export default function Page() {
  return (
    <ResourcePage
      eyebrow="CHAMPIONSHIP / CALENDAR"
      title="Race calendar"
      description="Schedule race events against a championship and circuit."
      endpoint="/events"
      columns={[
        "name",
        "championship_name",
        "circuit_name",
        "round_number",
        "start_date",
      ]}
      fields={[
        { name: "championship_id", required: true },
        { name: "circuit_id", required: true },
        { name: "round_number", type: "number", required: true },
        { name: "name", required: true },
        { name: "start_date", type: "datetime-local", required: true },
      ]}
    />
  );
}
