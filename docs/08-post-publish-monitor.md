# 08 — Post-publish Monitor + Backlash Playbook

ชิ้นที่ทำให้ Lane B/C/D มีคุณค่าจริง (เป็นแหล่ง ground truth สำหรับ calibrate)

## 3 หน้าที่
1. Early-warning — จับ backlash ในชั่วโมงแรก (ช่องโหว่ของดีไซน์เดิม)
2. Ground truth — ป้อนผลจริงกลับไป calibrate Lane B/C/D + Scores
3. Community (goal #3) — เข้าใจ comment → FAQ/requests/sentiment → idea backlog + ร่างตอบ

## หลักคิด
backlash = velocity + deviation จาก baseline ของช่องเอง ไม่ใช่ threshold ตายตัว →
anomaly detection เทียบ baseline. แยก "เผ็ดแต่สุขภาพดี (debate=แบรนด์)" ออกจาก "backlash จริง
(โกรธเป็นก้อน, call-to-action)" ด้วย LLM clustering ไม่ใช่แค่ polarity

## Data + cadence
sampling ถี่ตอนต้น เบาตอนหลัง: t+15m,+30m,+1h,+2h,+4h,+8h,+24h แล้วรายวัน ~1 สัปดาห์

| Platform | comment | metric | หมายเหตุ |
|---|---|---|---|
| YouTube | poll `commentThreads.list` (1 unit) | Analytics (views/like ratio/retention) | comment ต้อง poll |
| IG | `/{media-id}/comments` + webhooks | insights | ดีสุด real-time |
| TikTok | จำกัดมากผ่าน API | — | จุดอ่อนจริง → notification ในแอป + เช็คมือ |

sentiment/clustering → local LLM (bulk + privacy)

## Signals (ต่อคลิป ตามเวลา)
- engagement velocity เทียบ baseline
- negative-sentiment velocity = สัญญาณ backlash หลัก
- intent clustering: praise / correction ("well actually" = Lane C miss) / question(FAQ) / request / complaint / troll
- flag: factual-correction cluster, offense cluster, controversy spike

## Backlash playbook (tiered, human-in-loop เสมอ)
monitor เสนอ คุณตัดสิน — auto = draft + alert + log เท่านั้น; public action = คนกด

| Tier | สถานการณ์ | action |
|---|---|---|
| L0 | noise / debate สุขภาพดี | log |
| L1 | correction เล็ก (สเปกผิด) | ร่าง pinned แก้ + log เป็น Lane C miss → approve |
| L2 | negative cluster ขึ้น | alert เร็ว + ร่าง response + เสนอ pin |
| L3 | backlash เป็นก้อน / ข้อมูลผิดแพร่ / offense | urgent alert + options (pin, แก้ title/thumbnail, worst case unlist — คนตัดสิน) |

> ห้าม auto-reply ตอน backlash

## Calibration loop (keystone)
- correction comment → label Lane C จับ/พลาด → tune Lane C
- offense/tone backlash → label Lane A/B จับไหม → tune (ground truth ที่ Lane B รอ)
- performance จริง vs demand score → tune Score engine

## Community value
recurring question → FAQ + ไอเดียใหม่; "รีวิว X" → demand; ร่างตอบซ้ำ (approve); sentiment ต่อ pillar

## Reality checks
- TikTok = จุดอ่อน; แข็งสุด YouTube/IG
- ช่วงแรก baseline ยังไม่มี → โหมด learning (เก็บก่อน อย่า alert ดุ)
- privacy: comment = personal data → วิเคราะห์ local
- รันบน Pi heartbeat (poll) → enqueue → local LLM (Mac) → snapshot เข้า KB → alert

Schema: `schemas/monitor-snapshot.schema.json`
