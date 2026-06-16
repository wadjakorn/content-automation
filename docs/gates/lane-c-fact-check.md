# Lane C — Accuracy / fact-check (สำคัญสุดของช่องนี้)

ไม่ใช่ classifier แต่เป็น pipeline มาตรฐาน: claim detection → evidence retrieval → verdict (NLI) → explanation.
verdict สามทาง: SUPPORTED / REFUTED / NOT_ENOUGH_INFO (NEI). เคลมตัวเลข = ชนิดที่ตรวจยากสุด

## ยิง 2 จุด
- post-script (เคลมที่เขียน)
- post-edit จาก transcript (จับเคลม ad-lib ตอนถ่าย — จุดบอด)

## Pipeline
1. **Claim detection + check-worthiness** (local) — แตก atomic, คัดเฉพาะ verify ได้, ทิ้ง opinion/อนาคต
2. **Claim typing** → route:
   | ประเภท | verify กับ | เสี่ยง |
   |---|---|---|
   | spec/numeric | spec sheet/หน้า official | สูง |
   | price | ร้าน/หน้า official | volatile (timestamp+region) |
   | comparative | ข้อมูลสองฝั่ง + benchmark | สูง |
   | superlative/absolute | ยืนยันยากสุด | สูงสุด → flag แรง |
   | causal/technical | documentation | กลาง |
   | temporal | recency | กลาง |
3. **Evidence retrieval** — source เป็น tier (T1 official, T2 benchmark, T3 aggregator/cross-check);
   สร้าง "fact card" ต่อสินค้า cache เข้า KB → reusable (goal #2); ราคา TTL สั้น, สเปก TTL ยาว
4. **Verdict (NLI) ground จาก evidence เท่านั้น** — judge เทียบ claim vs evidence → SUPPORTED/REFUTED/NEI + source

> กฎเหล็ก: ไม่มี evidence → NEI → flag เสมอ ห้ามตอบ "น่าจะจริง". judge ต้อง quote evidence span; quote ไม่ได้ = NEI

## Decision
- SUPPORTED → pass + แนบ citation
- REFUTED + T1 ชัด → hold + ค่าที่ถูก + source
- NEI / source ขัดกัน → flag → human (ห้าม auto-เลือกข้าง)

Schema: `schemas/lane-c-factcheck.schema.json`

## Bonus value
SUPPORTED → auto-สร้าง sources+timestamps ลง description/pinned comment = credibility + ลด "well actually" + community trust;
fact cards สะสมใน KB (goal #2)

## Reality check
scope แคบ: เน้น numeric spec + price + superlative; ความเห็นอัตวิสัยอยู่นอก scope
