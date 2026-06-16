# 03 — Platform API Constraints (กำหนดสถาปัตยกรรม)

| ความสามารถ | YouTube (Data API v3) | Instagram (Graph API) | TikTok (Content Posting API) |
|---|---|---|---|
| Native scheduling | ✅ `status.publishAt` | ❌ create container → `media_publish` ทันที | ❌ ระบบยิงเอง |
| Auto-post สาธารณะ | ✅ | ✅ (ผ่าน Meta App Review: `instagram_content_publish`) | ⚠️ ติด app audit |
| ก่อนผ่าน audit/review | quota เท่านั้น | Business/Creator + ผูก FB Page | โพสต์ได้เฉพาะ SELF_ONLY, ≤5 users/24h |
| Rate / quota | 10,000 units/วัน; upload ~100 units (เดิม ~1600) | 50 โพสต์/24h, 200 req/hr/user | 6 req/นาที/token |
| ดึง comment | ✅ `commentThreads.list` (1 unit) | ✅ `/{media-id}/comments` + webhooks | ⚠️ จำกัดมาก |
| Caption upload (sidecar) | ✅ `captions.insert` SRT/VTT (~400 units) | ❌ ไม่มี track → burn-in | ⚠️ จำกัด → burn-in |
| Localized metadata | ✅ `localizations` (title/desc) | ❌ | ❌ |

## Implications
- YouTube offload scheduling ได้ → resilient ต่อบ้าน/ISP ล่ม ณ เวลาโพสต์
- IG/TikTok: scheduler ต้องตื่นยิงเอง
- TikTok public auto-post ติด audit → MVP draft-first
- IG ไม่มี native schedule + ต้องผ่าน App Review
- 🔜 (Phase 2) localization: YT = sidecar caption + localized metadata; IG/TikTok = burn-in subtitle (asset แยกต่อภาษา). ดู `docs/09-localization.md`

## Refs
- TikTok: https://developers.tiktok.com/doc/content-sharing-guidelines
- IG: https://developers.facebook.com/docs/instagram-platform/content-publishing/
- YouTube: https://developers.google.com/youtube/v3/revision_history
