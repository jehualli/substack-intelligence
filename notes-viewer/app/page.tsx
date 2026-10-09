import { redirect } from "next/navigation";

export default function Home({
  searchParams,
}: {
  searchParams: { restacks?: string };
}) {
  redirect(searchParams.restacks ? "/month?restacks=1" : "/month");
}
