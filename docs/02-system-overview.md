# 02 — System Overview (content-ops loop)

ระบบคือ content supply chain แบบวนลูป ไม่ใช่เครื่อง publish เดี่ยว ๆ:

```
Idea backlog → AI generation → Planning → Production → Publishing → Feedback → (calibration) → กลับเข้า backlog
```

- เบื้องหลังทุก stage มี knowledge base (Postgres + pgvector) ที่ AI generation อ่านไปใช้
  และ Feedback เขียนกลับเข้าไป → ทำให้ goal #2 (องค์ความรู้) และ #3 (community) เกิดจากตัวระบบเอง
- หลักการ: "1 idea → N outputs" (long-form, shorts×N, reel) = derivative assets จากต้นทางเดียว
- 🔜 (Phase 2) localization fan-out = derivative assets อีกแกน: 1 video → N language caption tracks + localized metadata. แทรก sub-stage `editing → [localize] → ready`. ดู `docs/09-localization.md`
