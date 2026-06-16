# 09 — Localization: Auto-Captions + Translation + Multi-Language

> Status: **🔜 Future plan (Phase 2)** — ออกแบบไว้ก่อน, **ยังไม่ build ใน Phase 0**.
> ข้อยกเว้นเล็ก ๆ ที่อนุญาตเข้า Phase 0 = §7 (source-lang caption เดี่ยว).

## 1. Framing — นี่คือ derivative-asset ไม่ใช่ pillar ใหม่
Auto-captions + translation + multi-lang = **localization fan-out** ของหลักการเดิม
`1 idea → N outputs` (ดู `docs/02-system-overview.md`). ต้นทางเดียว (video + audio) →
แตกเป็น N language tracks + localized metadata. กลไกเดียวกับ long-form→shorts.

ผลพลอยได้: source-lang caption เดี่ยว ๆ ก็ได้ accessibility + SEO + watch-time ฟรี
แม้ยังไม่ทำ multi-lang.

## 2. Pipeline placement — sub-stage ใหม่ `editing → [localize] → ready`
State machine เดิม (`CLAUDE.md`): `idea→scripted→filming→editing→ready→scheduled→published`.
แทรก `localize` คั่นระหว่าง `editing → ready`:

```
editing → [localize] → ready → scheduled → published
              │
   ┌──────────┼───────────────┐
   ASR        translate         package
 (transcript)(per target lang) (caption asset + localized metadata)
              │
        ┌─────┴─────┐
   gate re-check  (Lane A/B/C ต่อภาษา — ดู §4)
```

3 ขั้น:
1. **ASR** — audio → timed transcript (source lang)
2. **Translate** — source transcript → N target langs (+ localized title/description)
3. **Package** — แปลงเป็น 2 รูปทรงตามที่ platform รับ (ดู §5):
   - sidecar caption file (SRT/VTT) สำหรับ YouTube
   - burned-in subtitle render job สำหรับ IG/TikTok

## 3. Capability flags ต่อ adapter
เพิ่มเข้า per-platform adapter (หลักการ `CLAUDE.md` → capability flags):
- `supports_caption_upload` — platform รับ sidecar caption track ผ่าน API ไหม
- `supports_localized_metadata` — รับ localized title/description ไหม
- `subtitle_strategy` ∈ {`sidecar`, `burn_in`} — ไม่รองรับ sidecar → ต้อง burn-in ตอน render

| Platform | `supports_caption_upload` | `supports_localized_metadata` | `subtitle_strategy` |
|---|---|---|---|
| YouTube | ✅ (`captions.insert`) | ✅ (`localizations`) | `sidecar` |
| Instagram | ❌ | ❌ | `burn_in` |
| TikTok | ⚠️ จำกัด | ❌ | `burn_in` |

## 4. SAFETY — translated text = new content (กฎเหล็ก)
Machine translation ทำลาย hard rules ของ `CLAUDE.md` แบบเงียบ ๆ. **source ผ่าน gate ≠ translation ผ่าน**.
ทุก translated track ต้อง **re-enter Lanes A/B/C ในภาษาของตัวเอง** ก่อน track นั้น ship.

- **Health/medical claim → HOLD เสมอ** (อย./อาญา). MT สร้างเคลมแรงกว่าต้นทางได้
  → keyword scan health terms ต่อภาษา; เจอ = HOLD, ห้าม auto-publish track นั้น.
  (ดู `docs/gates/lane-c-fact-check.md`, hard rule ใน `CLAUDE.md`)
- **Brand voice (Lane B)** — tone ไม่รอดข้ามภาษา. "คมแต่มีเหตุผล" แปลแล้วอาจกลายเป็น
  condescension / punching-down. Re-run Lane B ต่อภาษา. (`docs/gates/lane-b-tone-brand.md`)
- **Disclosure (Lane D)** — sponsored/gifted/affiliate disclosure ต้องรอดการแปล.
  disclosure หาย/เพี้ยนในภาษาเป้าหมาย = block track. (`docs/gates/lane-d-context-timing.md`)
- **Fact (Lane C)** — ตัวเลข/สเปก/ชื่อรุ่น corrupt ได้ตอนแปล → re-check.

Cascade เดิม: keyword (ถูก) → LLM-judge ต่อภาษา (แพง) → human HOLD. ไม่มี evidence/ไม่ชัด = flag.

## 5. Platform reality (กำหนด output shape)
- **YouTube** — full multi-lang: `captions.insert` อัป SRT/VTT ต่อภาษา (~400 units/track) +
  `localizations` ใส่ localized title/description. ไม่ต้อง re-render video.
- **Instagram** — ไม่มี multi-track API → ต้อง **burn-in** subtitle ลง render เป็น asset แยกต่อภาษา.
- **TikTok** — subtitle API จำกัด → burn-in เช่นกัน. ระวัง app-audit constraint (ดู `docs/03`).

→ `localize` stage ต้อง emit ได้ทั้ง sidecar files (YT) และ burn-in render jobs (IG/TikTok).

## 6. Tech (local-first, ตาม `docs/04-infra-hybrid.md`)
- **ASR**: Whisper local บน Mac M5 — ฟรี, private, ไม่ต้องอัป media ที่ยังไม่ปล่อยขึ้น cloud.
  Output = timed transcript (SRT/VTT).
- **Translate**: local LLM ก่อน (cascade) → cloud API fallback สำหรับภาษาที่ต้องคุณภาพสูง.
- **Storage**: caption assets + burn-in renders เก็บบน NAS DS723+.
- **Quota**: YouTube `captions.insert` ~400 units/track → คุม budget ต่อวัน (10,000 units cap).

## 7. ข้อยกเว้นที่อนุญาตเข้า Phase 0 (cheap, near-zero risk)
**source-lang caption เดี่ยว** เท่านั้น: Whisper → SRT → `captions.insert` (ภาษาต้นทาง, ไม่แปล).
- ไม่มี translation → ไม่มี Lane re-check ซับซ้อน
- ได้ accessibility + SEO + watch-time
- risk ต่ำ (ไม่สร้างเคลมใหม่)

Multi-lang/translation จริง = **Phase 2** พร้อม multi-platform fan-out. อย่า build ก่อน.

## 8. Open questions (decide ตอนเข้า Phase 2)
- เลือกภาษาเป้าหมายจาก analytics จริง (audience geo) ไม่ใช่เดา
- Burn-in render = pipeline cost จริง → คุ้มเฉพาะคลิปที่ demand สูง?
- Human review ต่อภาษา scale ยังไง (ไม่มี native ตรวจทุกภาษา) → trusted-MT + spot-check?
