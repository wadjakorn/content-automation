# Lane B — Tone/Brand "bad attitude" (advisory เท่านั้น)

กฎเหล็ก: **flag + อธิบาย ไม่เคย block** (ไม่งั้น sand บุคลิกช่องทิ้ง). นี่คือ brand-voice consistency ไม่ใช่ policy

## Pattern (ไม่ใช่ "attitude" ลอย ๆ)
| Pattern | ปัญหา | คือแบรนด์ (ไม่ใช่ปัญหา) |
|---|---|---|
| Condescension | ข่มคนดู | อธิบายของยากให้ง่าย |
| Punching-down | กดคนอ่อนกว่า | วิจารณ์บริษัทใหญ่ที่พลาด |
| Gatekeeping | tech-bro elitism | ตั้งมาตรฐานเทคนิคมีเหตุผล |
| Unwarranted absolutism | "X ขยะ ใครซื้อโง่" | "X ไม่คุ้มเพราะ a,b,c" |
| Sneer | เหยียดไร้สาระรองรับ | ความเห็นแรงมีหลักฐาน |

> คอลัมน์ขวา = สินทรัพย์ของช่อง — แยก "คม on-brand" ออกจาก "ข่ม/เหยียดเผลอ"

## ทำไมไม่มี classifier สำเร็จรูป
toxicity classifier จับไม่ได้ (สุภาพระดับคำ ผิดระดับ tone) → LLM-as-judge ล้วน + rubric จาก brand voice เราเอง
(ground truth = brand voice spec ใน CLAUDE.md + RAG เหนือ transcript เก่า: เทียบคลิป comment สุขภาพดี vs ทัวร์ลง)

## จุดที่รัน
post-script เป็นหลัก; เช็คเบา post-edit (น้ำเสียง VO, ข้อความบนจอ) + title/thumbnail (ragebait framing)

Schema: `schemas/lane-b-advisory.schema.json` — severity สูงสุดแค่ `medium`, ไม่มี block

## Calibration = หัวใจ
correlate flag กับ backlash จริง (จาก post-publish monitor) → pattern ทำนายได้เก็บ, ไม่สัมพันธ์ตัดทิ้ง.
default under-flag (จู้จี้แล้วจะถูกปิดทิ้ง). ROI จริงเกิดหลัง monitor พร้อม
