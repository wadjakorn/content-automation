# Lane A — Policy/Safety (hard, auto-block ได้)

map กับ YouTube hate speech + advertiser-friendly guidelines (เงินเหลือง/strike)

**ขอบเขต:** โจมตี protected attributes (เชื้อชาติ/ศาสนา/ชาติพันธุ์/เพศ/รสนิยมทางเพศ/ความพิการ),
slur, dehumanization, ขู่ทำร้าย — *ไม่ใช่* accuracy(C)/tone(B)/timing(D)
**ความเสี่ยงจริง:** ความเผลอ (analogy loaded, มุกเหยียดไม่ตั้งใจ, slur ในคลิปที่ยกมาอ้าง,
ข้อความบนจอ, thumbnail) → cover surface ที่ไม่ใช่สคริปต์สำคัญกว่าตัวสคริปต์

## ยิง 2 จุด
- post-script: สคริปต์, VO, ข้อความบนจอ planned, title/desc ร่าง
- post-edit + metadata: transcript (whisper), OCR ข้อความบนจอ/ซับ, thumbnail (vision), title/desc/tags

## Cascade
| Tier | ตัวตรวจ | บทบาท | หมายเหตุ |
|---|---|---|---|
| 0 | lexicon/slur + regex (รวมไทย) | ยกธงให้ judge | ห้าม block เดี่ยว (FP สูงกับ quote/reclaimed) |
| 1 | classifier ถูก | กรองชั้นแรก | ดูหมายเหตุด้านล่าง |
| 2 | LLM-as-judge (frontier) + rubric | ตัวตัดสินจริง | คืน stance + evidence + fix |
| 3 | human (คุณ) | gray band | เหลือเฉพาะที่ judge ไม่มั่นใจ |

**Tier 1:** Perspective API เป็น baseline (TOXICITY, SEVERE_TOXICITY, IDENTITY_ATTACK, INSULT, PROFANITY, THREAT)
แต่ (1) Google wind down ปี 2026 (2) ภาษาอื่นแม่น ~60–75% อ่อนกับ sarcasm (3) ไร้บริบท + bias AAVE/LGBTQ+
→ คอนเทนต์ไทย+hybrid ใช้ **Llama Guard (local) หรือ OpenAI Moderation**; ตัวตัดสินจริง = Tier 2 judge multilingual

## หัวใจ logic: ตัดสินที่ stance ไม่ใช่ score
- `endorsing`/`attacking` ชัด → hold (auto-block เฉพาะ slur+attack ที่ไม่กำกวมล้วน ๆ)
- `discussing`/`quoting`/`criticizing` → pass
- ไม่มั่นใจ → flag → human
- solo creator: default "hold + เด้งให้ดู" > auto-block เงียบ

Schema: `schemas/lane-a-verdict.schema.json`

## Calibrate
log hold/flag เทียบผลจริง (pass แล้วโดน strike = FN แพงสุด); จับ FP rate เฉพาะ quote/วิจารณ์; ค่อยลด threshold เมื่อเชื่อ judge
