# CDP — Customer Data Platform cho Du lịch

Hệ thống CDP tự host hoàn chỉnh cho doanh nghiệp du lịch Việt Nam.

## Kiến trúc

```
Loyalty DB ─────┐
Sales DB ────────┼─── Batch ETL (APScheduler)
Website SDK ─────┼─── Collector API (FastAPI) → Redis Streams
Mobile SDK ──────┘
                          │
                    Celery Processor
                  (identity resolution)
                          │
                    PostgreSQL CDP Schema
                    (profiles, events, segments)
                          │
               ┌──────────┴──────────┐
          Segmentation          Admin API + UI
          Engine (SQL)          (FastAPI + Next.js)
               │
          Activation Layer
          (SendGrid / eSMS / Meta Ads)
```

## Khởi động nhanh

```bash
cp .env.example .env
# Điền LOYALTY_DB_URL, SALES_DB_URL, JWT_SECRET_KEY, SENDGRID_API_KEY...

make setup
# Tương đương: docker compose build → alembic migrate → npm build SDK → docker compose up
```

Truy cập:
- Admin UI: http://localhost:3000
- Admin API docs: http://localhost:8002/docs
- Collector API: http://localhost:8001

## Nhúng tracking SDK lên website

```html
<!-- Thêm vào <head> của website -->
<script>
!function(){
  var cdp=window.cdp=window.cdp||[];
  if(cdp.initialized)return;
  /* ... xem sdk/js/snippet.html để lấy snippet đầy đủ ... */
  cdp.load("YOUR_WRITE_KEY", { collectorUrl: "https://collect.yourdomain.com" });
  cdp.page();
}();
</script>
```

Lấy `write_key` tại: Admin UI → Nguồn dữ liệu → Tạo nguồn.

## Cấu hình kết nối Loyalty & Sales

Trong `.env`:
```
LOYALTY_DB_URL=postgresql://user:pass@loyalty-host:5432/loyalty_db
SALES_DB_URL=postgresql://user:pass@sales-host:5432/sales_db
```

Adapt SQL queries trong:
- `services/ingestion/app/connectors/loyalty_pg.py` — điều chỉnh tên bảng/cột
- `services/ingestion/app/connectors/sales_pg.py` — điều chỉnh tên bảng/cột

## Tạo Segment ví dụ

```json
{
  "name": "VIP đặt Đà Nẵng 6 tháng",
  "rules": {
    "operator": "AND",
    "conditions": [
      {"field": "traits.tier", "op": "eq", "value": "gold"},
      {
        "field": "events.booking_completed.destination",
        "op": "contains",
        "value": "Đà Nẵng",
        "time_window": {"last_n_days": 180}
      },
      {"field": "traits.total_spend_vnd", "op": "gte", "value": 10000000}
    ]
  }
}
```

## Các giai đoạn triển khai

| Phase | Nội dung | Thời gian |
|-------|----------|-----------|
| 1 | Foundation: schema, batch ETL, profile explorer | Tuần 1–6 |
| 2 | Behavioral tracking: Collector API, JS SDK, identity resolution | Tuần 7–12 |
| 3 | Segmentation & Activation: SendGrid, eSMS, Meta Ads | Tuần 13–20 |
| 4 | Analytics, Mobile SDK, monitoring, hardening | Tuần 21–26 |

## Cấu trúc dự án

```
services/
  collector/      — Event Collector API (FastAPI)
  processor/      — Celery event processor + identity resolution
  ingestion/      — Batch ETL từ loyalty & sales
  segmentation/   — Segmentation engine (SQL builder)
  activation/     — SendGrid, eSMS, Meta Ads destinations
  api/            — Admin API (FastAPI + JWT)
  ui/             — Admin UI (Next.js 14)
shared/           — SQLAlchemy models, Pydantic schemas dùng chung
sdk/js/           — Browser tracking SDK (TypeScript)
migrations/       — Alembic schema migrations
infra/            — nginx, postgres init
```
