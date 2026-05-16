# CURSOR_WORKLOG — shared worklog

**Repo:** https://github.com/HugoLeon1199/Crawl-Web-Repository  
**Project:** Leon Global Web Intelligence Engine  

Single shared AI workflow file — Leon, ChatGPT, Gemini ↔ Cursor.  
Do **not** spawn parallel long workflow docs; this file + code/comments carry intent.

---

## Current session (2026-05-16) — auto Git sync policy + push

### Current task

Leon: Cursor **tự cập nhật worklog** sau khi sửa và **commit + push** lên GitHub **không cần nhắc**. Resolve merge với stub worklog cũ trên remote; giữ nội dung chi tiết + rule auto-push.

### Files created

- *(remote đã có `.ai/` stub template — đã merge/replace bằng nội dung đầy đủ bên dưới)*

### Files modified

- `.cursor/rules/cursor-worklog.mdc` — **commit + push** sau thay đổi có ý nghĩa (trừ khi Leon nói không push).
- `.ai/CURSOR_WORKLOG.md` — merge conflict resolved (stub GitHub ↔ bản chi tiết Cursor).
- `leon_web_intel/config/crawl_rules.yaml` — `user_agent` = `LeonWebIntelBot/0.1 (+local research project)`.
- `leon_web_intel/src/settings.py` — fallback `user_agent` khớp charter.

### Files deleted

- *(none)*

### What was implemented

- Chính sách **tự động đẩy GitHub** sau chỉnh sửa đáng kể (rule + worklog).
- `git pull --rebase` + resolve **add/add** conflict trên `CURSOR_WORKLOG.md`.

### How to run

```bash
cd leon_web_intel
python run_profile.py --input config/sources_raw.txt --dry-run
```

### How to test

```bash
cd leon_web_intel
python -m pytest
```

### Test result

- **Not run** in this Cursor turn.

### Known issues

- None specific to this Git/policy update.

### Risks

- Auto-push cần credential local OK; nên có branch protection nếu team lớn.

### Notes for ChatGPT review

- Agent-initiated pushes — confirm policy with Leon; PR-only workflow alternative.

### Notes for Gemini review

- Optional `pre-push` pytest hook later.

### Next suggested step

- `pytest` + `profile-only --limit 10` sau khi pull.

---

## Archive — charter alignment (2026-05-16)

- Inspect Tầng 0–11 vs `leon_web_intel/`; mapping charter ↔ code — xem git history (`0625a30` era / earlier commits).

## Archive — rules bootstrap

- Khởi tạo `.cursor/rules/cursor-worklog.mdc` và worklog.
