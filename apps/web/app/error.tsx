"use client";
export default function Error({ reset }: { reset: () => void }) {
  return (
    <div role="alert">
      <h1>Không thể hiển thị trang</h1>
      <p>Vui lòng thử tải lại.</p>
      <button onClick={reset}>Thử lại</button>
    </div>
  );
}
