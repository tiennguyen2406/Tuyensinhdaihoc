# T09 internal DEV smoke release — 19/10/2026

Implementation: `services/data/releases`, migration additive `0004_releases`, dedicated
release capability và CLI. Contract/runbook: ../release-contract.md; kế hoạch:
../plans/2026-10-19-t09-release-pilot.md. Không đổi facts hoặc approvals A2/B/C/D.

Baseline kiểm thực tế: branch codex/crawler-pilot, HEAD4ad84c3cd0878a85d8fd0ac809e09c1e7e091747,
origin đúng repository; chỉ .vscode/ untracked trước implementation. Spec gốc SHA-256
c3745329543e433bd62cf58e4a6df4c827ea54b5876f48f8c42e33d5aabf04c5 khớp provenance.
Schema0003, catalog3, canonical3 đúng ba UUID publication, observations863/jobs55/audit36,
releases0, refresh1/2/3 queued. Private baseline giữ row/file digests.

Tests T09 synthetic riêng đã kiểm snapshot/count/fidelity, publication race, concurrent
workers, replay, checksum/missing file, write/register/finalization failures, orphan recovery,
expired lease/fencing, registered-release job recovery, DB guards và real CLI/reader denial.
Review độc lập đã xác nhận các sửa recovery/NULL guards/provenance; không còn blocker.

**DEV release chưa chạy tại checkpoint implementation này.** Kết quả vận hành và CI exact SHA
sẽ được ghi trong checkpoint báo cáo kế tiếp, không suy từ code hoặc tests thành release thật.
