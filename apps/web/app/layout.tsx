import type { Metadata } from "next";
import Link from "next/link";
import "./globals.css";

export const metadata: Metadata = {
  title: "Tra cứu tuyển sinh · Nội bộ",
  description:
    "Tra cứu trường, chương trình tuyển sinh và điểm chuẩn theo nguồn đã xác minh.",
};
export default function Layout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="vi">
      <body>
        <a className="skip-link" href="#main">
          Đến nội dung chính
        </a>
        <header>
          <Link
            prefetch={false}
            className="brand"
            href="/universities?year=2024"
          >
            <span className="brand-mark" aria-hidden="true">
              ĐH
            </span>
            Danh mục tuyển sinh
          </Link>
          <span className="dev-badge">Nội bộ · DEV</span>
          <nav aria-label="Tra cứu tuyển sinh">
            <Link prefetch={false} href="/universities?year=2024">
              Trường đại học
            </Link>
            <Link prefetch={false} href="/majors?year=2024">
              Ngành/chương trình
            </Link>
          </nav>
        </header>
        <main id="main">{children}</main>
        <footer>
          Thông tin chỉ phản ánh phạm vi đã thu thập và xác minh. Đối chiếu
          thông báo chính thức của trường.
        </footer>
      </body>
    </html>
  );
}
