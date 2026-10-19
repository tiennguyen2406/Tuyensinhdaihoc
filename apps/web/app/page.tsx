import { redirect } from "next/navigation";
export default function Home() {
  redirect("/universities?year=2024");
}
