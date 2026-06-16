# CLAUDE.md — project context (read this first, every session)

Keep this file small and durable. Detailed design lives in `docs/`. This file is the
fixed context + rules Claude should always honor when working in this repo.

## What this is
ระบบ + automation สำหรับวางแผน/ผลิต/เผยแพร่/เก็บ feedback คอนเทนต์ข้ามแพลตฟอร์ม
(YouTube, TikTok, Instagram; เพิ่มแพลตฟอร์มได้ภายหลัง). Owner = solo creator + SWE (~9y),
อดีตช่องรีวิว IT/gadget (~8k subs, ทิ้งร้าง ~2 ปี).

## Goals (priority order)
1. รายได้เสริม → รายได้หลัก
2. สร้างองค์ความรู้ (knowledge base)
3. สร้าง community

## Content pillars (weight สูง → ต่ำ)
1. technology *(เน้น)*  2. ai/agent/automation *(เน้น)*  3. gadgets  4. lifestyle  5. longevity/healthcare

## Brand voice spec (seed — ใช้เป็น ground truth ของ Lane B + การ generate)
On-brand = คมแต่มีเหตุผลรองรับ, อธิบายของยากให้ง่าย, วิจารณ์บริษัทใหญ่ที่พลาดได้.
Off-brand (ห้าม) = ข่มคนดู (condescension), กดคนที่อ่อนกว่า (punching-down),
tech-bro gatekeeping, absolutism ลอย ๆ ("X ขยะ ใครซื้อโง่"), เหยียดแบบไร้สาระรองรับ.
> ขยาย/ปรับ spec นี้จาก transcript จริง (เทียบคลิป comment สุขภาพดี vs ทัวร์ลง)

## Hard rules (non-negotiable)
- **Health/medical claims about a product → HOLD เสมอ ห้าม auto-publish.** (อย.: รีวิวเพื่อการค้า = โฆษณา; เคลมเกินจริงมีโทษอาญา)
- **Sponsored/gifted/affiliate → ต้อง disclose** (YouTube paid-promotion toggle + พูด/เขียน). disclosure หาย = block.
- ใช้ official platform API เท่านั้น — ห้าม UI automation/scraping (Selenium/Playwright posting) เพราะเสี่ยงโดนแบนบัญชี.
- ห้าม commit secrets (OAuth tokens, API keys, .env) หรือ media ลง git.
- Fact-check verdict ต้อง ground จาก evidence ที่ retrieve เท่านั้น — ไม่มี evidence = NOT_ENOUGH_INFO → flag, ห้ามตอบ "น่าจะจริง".

## Architecture decisions (settled)
- **Local-first hybrid**: Mac M5 = compute + local LLM · NAS DS723+ = media/backup · Pi 4B = always-on scheduler/heartbeat · Cloudflare Tunnel = ingress เดียว (webhooks/OAuth).
- **Scheduling**: YouTube ใช้ `status.publishAt` (offload ให้แพลตฟอร์ม). IG/TikTok ระบบยิงเอง.
- **TikTok**: ติด app audit → MVP draft/private auto + manual publish.
- **IG**: ต้องผ่าน Meta App Review + Business/Creator + FB Page; ไม่มี native schedule.
- Build/ops assistant (Claude Code) ≠ runtime. ระบบ production รันเป็น service บน Mac/Pi เอง.

## Engineering principles
- Cascade ทุก check: ถูก (keyword/local) → แพง (LLM-judge + retrieval) → คน.
- Calibrate ทุก gate/score เทียบ ground truth จริง แล้วตัดสัญญาณที่ไม่เวิร์กทิ้ง.
- Human-in-the-loop เป็น default สำหรับ soft signals; auto เฉพาะ hard policy ที่ชัด.
- Structured verdict (JSON) ทุก gate — ดู `schemas/`.
- Per-platform adapter + capability flags (`supports_native_schedule`, `requires_audit`, `can_fetch_comments`).
- Content item เป็น explicit state machine: `idea→scripted→filming→editing→ready→scheduled→published`.

## Working agreements for Claude in this repo
- ออกแบบ/แก้ไฟล์ใน `docs/` และ `schemas/` ได้; ถามก่อนทำอะไรที่ลบ/เขียนทับเยอะ ๆ.
- เวลาเพิ่ม design ใหม่ ให้เขียนลงไฟล์ที่เกี่ยวข้อง + อัปเดต `README.md` index.
- ยังอยู่ช่วง design → build phase 0; อย่า over-engineer เกิน phase ปัจจุบัน (ดู `docs/06-build-phases.md`).

## Repo map
- `docs/` — design doc แตกเป็นหัวข้อ; `docs/gates/` = guardrail lanes A–D
- `schemas/` — JSON contract ของ gate verdicts
- `diagrams/` — mermaid source + FigJam links
- `build/` — docker-compose / adapters (TODO, phase 0+)
