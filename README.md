# Content Automation System

Living design + (eventually) implementation ของระบบ automate การวางแผน/ผลิต/เผยแพร่/
เก็บ feedback คอนเทนต์ข้ามแพลตฟอร์ม.

> Status: **Design** (Gates A–D ครบ, infra/flow ครบ) · กำลังจะเข้า build phase 0
> เปิด repo นี้ด้วย **Claude Code** แล้วเริ่มที่ `CLAUDE.md`

## Index
| ไฟล์ | เนื้อหา | สถานะ |
|---|---|---|
| `CLAUDE.md` | context + rules ตายตัว (อ่านทุก session) | ✅ |
| `docs/01-context-goals.md` | owner, pillars, goals, scale | ✅ |
| `docs/02-system-overview.md` | content-ops loop | ✅ |
| `docs/03-platform-constraints.md` | ข้อจำกัด API จริง (YT/IG/TikTok) | ✅ |
| `docs/04-infra-hybrid.md` | local-first hybrid + topology | ✅ |
| `docs/05-pipeline-gates-scores.md` | flow + Gate/Score model | ✅ |
| `docs/gates/lane-a-policy-safety.md` | racism/religion/hate (hard) | ✅ |
| `docs/gates/lane-b-tone-brand.md` | "bad attitude" (advisory) | ✅ |
| `docs/gates/lane-c-fact-check.md` | accuracy (สำคัญสุด) | ✅ |
| `docs/gates/lane-d-context-timing.md` | disclosure/sensitivity/consistency | ✅ |
| `docs/06-build-phases.md` | phase 0–3 | ✅ |
| `docs/07-open-decisions.md` | risks + next | ✅ |
| `docs/08-post-publish-monitor.md` | backlash monitor + calibration keystone | ✅ |
| `docs/09-localization.md` | auto-caption + translation + multi-lang (future plan, Phase 2) | 🔜 |
| `docs/superpowers/specs/2026-06-16-stack-tools-design.md` | phase-0 stack & tools (settled) | ✅ |
| `docs/superpowers/plans/2026-06-16-phase0-consistency-engine.md` | phase-0 build plan | ✅ |
| `schemas/` | JSON verdict contracts | ✅ |
| `diagrams/` | high-level flow + stack architecture + deploy topology (mermaid) | ✅ |
| `build/` | Dockerfile + docker-compose (Pi 4B stack) | ✅ |

## Next design targets (ยังไม่ทำ)
- score engine (สูตร priority + แหล่งสัญญาณ demand)
- sub-flow diagrams ต่อ lane
- docker-compose topology บน Mac+NAS
- localization fan-out (Phase 2) — ดู `docs/09-localization.md`

## How to use with Claude Code
```
cd content-automation
claude          # Claude Code จะอ่าน CLAUDE.md อัตโนมัติ
```
แล้วสั่งงานได้เลย เช่น "ออกแบบ post-publish monitor แล้วเขียนลง docs/" หรือ
"เริ่ม scaffold build/ ตาม phase 0".
