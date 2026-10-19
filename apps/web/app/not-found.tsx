export default function NotFound() {
  return (
    <>
      <h1>Không tìm thấy trang</h1>
      <Link prefetch={false} href="/universities?year=2024">
        Trở về danh sách trường
      </Link>
    </>
  );
}
import Link from "next/link";
