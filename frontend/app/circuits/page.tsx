import { ResourcePage } from "@/components/resource-page";
export default function Page() {
  return (
    <ResourcePage
      eyebrow="CHAMPIONSHIP / VENUES"
      title="Circuits"
      description="Maintain circuit locations and measured lap distances."
      endpoint="/circuits"
      columns={["name", "country", "length_km"]}
      fields={[
        { name: "name", required: true },
        { name: "country", required: true },
        { name: "length_km", type: "number", required: true },
      ]}
    />
  );
}
