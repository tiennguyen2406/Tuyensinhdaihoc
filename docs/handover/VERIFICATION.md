# Kiểm chứng bộ bàn giao

Chỉ chạy smoke bên dưới với **DB mới, catalog rỗng**. Script cố ý fail nếu có business data, không dùng nó để nghiệm thu DBDEV cũ.

```powershell
python scripts/verify_handover.py --api http://127.0.0.1:8000 --web http://127.0.0.1:3000
```

Không có Python trên host thì chạy Python có sẵn trong image:

```powershell
docker compose exec api python -m scripts.verify_handover --api http://api:8000 --web http://web:3000
```

Kiểm live/ready, API catalog, proxy và trang `/majors`; catalog phải HTTP200/items=[] chứ không phải502/503. Script này là HTTP smoke của installation rỗng, không real advice E2E, không kiểm đầy đủ mobile UI hoặc legal rights.

Reader assertions và idempotence được kiểm bằng `tests/test_docker_bootstrap.py` trên database test riêng. Với stack bàn giao mới:

```powershell
docker compose run --rm --no-deps init python -m pytest tests/test_docker_bootstrap.py -q
```

Xem report task để biết checks thực tế và giới hạn. Không coi việc có file test là bằng chứng test đã chạy. Không chạy fixture qua credential DEV cũ hoặc owner dùng cho DB có dữ liệu nghiệp vụ.
