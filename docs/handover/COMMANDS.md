# Lệnh bàn giao và Git

Chạy ở root repository. Bộ mới dùng Docker Compose v2; README là hướng dẫn chính.

```powershell
git clone --branch codex/crawler-pilot https://github.com/tiennguyen2406/Tuyensinhdaihoc.git
cd Tuyensinhdaihoc
Copy-Item .env.example .env
# Điền ba secrets riêng trong .env trước khi chạy:
docker compose up -d --build
docker compose ps -a
docker compose logs --tail=100 init api web
```

Khi sửa đúng bộ bàn giao, review và stage exact files sau (không stage `.env`, state hoặc settings cá nhân):

```powershell
git status --short
git diff --check
git add -- .env.example .gitignore .dockerignore .gitattributes .vscode/extensions.json .github/workflows/ci.yml docker-compose.yml Dockerfile apps/web/Dockerfile apps/web/tests/proxy.test.ts requirements.txt README.md HANDOVER.md scripts/docker_bootstrap.py scripts/verify_handover.py tests/test_docker_bootstrap.py docs/operator-pipeline.md docs/handover/COMMANDS.md docs/handover/VERIFICATION.md docs/reports/docker-handover-20261022.md docs/reports/progress-20261022.md
git diff --cached --stat
git diff --cached --check
git commit -m "build: add reproducible Docker developer handover"
git push origin codex/crawler-pilot
git rev-parse HEAD
git ls-remote origin refs/heads/codex/crawler-pilot
```

Chỉ thêm tên file khi nó thực sự thuộc diff. Không force-push/merge/deploy. Mở Actions trên GitHub, kiểm eventpush và cả checks/web success cho đúng SHA. Auth/network bị chặn thì giữ local commit và báo thật, không gọi là đã push.

ZIP bàn giao được tạo từ exact Git blobs của commit đã bàn giao, giữ cấu trúc folder, kèm manifest SHA256 và commit link. ZIP chỉ là bộ tài liệu/config; kỹ sư clone repository để có toàn source code. Không dùng zip nguyên working directory vì có thể đưa secrets/raw/cache vào. Nếu đã clone đúng commit thì không cần chép đè files từ ZIP.

Cập nhật requirements sau đổi lockfile bằng uv0.13.1:

```powershell
uv export --frozen --no-dev --no-emit-project --format requirements.txt --output-file requirements.txt
```

Docker lấy dependency từ pyproject.toml/uv.lock và package.json/pnpm-lock.yaml. Không thay lock hoặc version trong quá trình bàn giao chỉ để bỏ qua build failure.
