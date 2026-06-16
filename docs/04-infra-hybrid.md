# 04 — Deployment: Local-first Hybrid

## Inventory
- Home server: Raspberry Pi 4B (ตอนนี้) → Mac mini Pro / Studio M5
- NAS: Synology DS723+ (2-bay, 2×2TB; RAM ถึง 32GB ECC; M.2 NVMe 2 ช่องทำ storage pool; DX517 ถึง 7 ลูก; ไม่เหมาะ transcoding)
- UPS: เพียงพอ graceful shutdown

## Topology
- ในบ้าน (UPS-backed): Mac M5 = compute + local LLM · NAS = media + backup · Pi = always-on scheduler/heartbeat
- Ingress: Cloudflare Tunnel / Tailscale Funnel = ประตูเดียวขาเข้า (webhooks/OAuth), outbound-only, CGNAT-proof
- External: Platform APIs, Frontier API (Claude/ChatGPT)

## What runs local
Postgres+pgvector (Mac, Pi ช่วงแรก) · MinIO/SMB บน NAS · job queue (BullMQ/Celery) ·
n8n→Temporal · local LLM (Ollama/MLX) · whisper · ffmpeg encode บน Mac · Btrfs snapshot บน NAS

## 3 constraints + ทางแก้
1. Inbound (OAuth/webhooks) → Cloudflare Tunnel / Tailscale Funnel
2. Availability ตอน publish → YouTube `publishAt`; IG/TikTok ใช้ Pi heartbeat 24/7 + retry; option cloud worker จิ๋ว (UPS กันไฟ ไม่กัน ISP)
3. Bandwidth/ความจุ → 2×2TB RAID1 ≈ ~2TB usable; tiering (NVMe=DB/hot, HDD=media, archive raw หลัง publish); encode บน Mac

## LLM routing (hybrid)
- Local: dedup/tag idea, สรุป comment, transcription
- Frontier: final script, storyboard, hook/title

## Staged rollout
- Pi4B ตอนนี้: Postgres + n8n/queue + cloudflared; LLM = frontier; ทำ phase 0
- Mac M5 มา: ย้าย compute + local LLM ขึ้น Mac; ลด Pi เป็น heartbeat/tunnel 24/7
- NAS: storage + backup ตั้งแต่วันแรก
