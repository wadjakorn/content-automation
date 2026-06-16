# 05 — Content Quality Pipeline: Gates & Scores

## หลักการ: แยก Gate ออกจาก Score
| | Gate | Score |
|---|---|---|
| หน้าที่ | ลดความเสี่ยง (กันของแย่) | เพิ่มโอกาส (จัดลำดับของดี) |
| ตัดสิน | block/flag (+เหตุผล) | ranking (advisory) |
| bias | recall (ยอม FP) | input ช่วยคิด ห้าม auto-decide |

ดู flow ที่ `diagrams/high-level-flow.mmd`

## Scores (ต้นน้ำ: intake + planning)
- fit — match persona + pillar weights (กัน drift)
- demand *(เดิม "social famous")* — สัญญาณจริง (Trends, search suggest, ยอดวิวคู่แข่ง, หัวข้อคล้ายในช่องเรา); virality ทำนายไม่ได้ อย่าเชื่อเลขเดียว
- novelty *(เดิม "creativity")* — มุมตัน/คนทำเยอะ/hook ใหม่พอไหม → ต้อง competitor scan
- effort/cost *(เพิ่ม)*
- timing — แกนแยก ใช้ตอน schedule

> Priority ≈ `f(fit, demand, novelty) ÷ effort`

## Gates — 4 lanes (ดู docs/gates/)
- A Policy/Safety (hard) · B Tone/Brand (advisory) · C Accuracy (fact-check) · D Context/Timing
- "backlash prevent" = synthesis ของ B+C+D เป็น reputational_risk เดียว (ไม่ใช่ check ปฐมภูมิ)

## Gates ยิง 3 จังหวะ
1. post-script (ถูกสุดที่จะแก้)
2. post-edit + metadata (title/thumbnail = จุดบอด backlash)
3. post-publish monitor (backlash จริงเกิดชั่วโมงแรก) — 🔜 ยังไม่ออกแบบ
