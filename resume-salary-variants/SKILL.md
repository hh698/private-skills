---
name: resume-salary-variants
description: Use when revising a two-page Chinese test-engineer resume PDF in an existing sidebar layout, resolving PDF annotation feedback, checking wording and page layout, or creating salary-specific application variants while preserving all other content.
---

# Test Engineer Resume PDF Template

Use the supplied resume PDF as the layout anchor. Preserve its module order, visual hierarchy, page count, and factual scope; improve wording only when the source supports it.

## Workflow

1. Extract text and render every source page before editing. Record the page count, section order, sidebar colors, font sizes, and the exact location of each field to replace.
2. Build or revise in the source style. Keep the usual order: basic information, job intention, self-evaluation, education, skills, work experience, projects. Do not invent employers, projects, metrics, tools, or responsibilities.
3. For test-engineer content, organize skills as: quality process, database/OS, network capture and diagnosis, API testing, automation/CI, performance, and AI-assisted testing. Describe AI as assisted script/data/scenario/log work, never as a replacement for testing judgment.
4. Treat PDF comments as layout requirements. Fix the specific short last line, cramped leading, title spacing, weak contrast, or wording issue; then re-render both pages and inspect nearby content for regressions.
5. Read the complete final text for typos, punctuation, time-format consistency, unsupported claims, and awkward phrasing. Render every final page. Deliver only when page count, legibility, alignment, and clipping checks pass.

## Two-page layout rules

| Area | Required outcome |
|---|---|
| Sidebar | Keep background, heading hierarchy, and contact/job-intention placement stable. |
| Self-evaluation | Match basic-information body font size; keep bullets balanced without changing established leading. Expand source-supported wording rather than force a 1-4-character final line. |
| Skills and work history | Keep section-title gaps consistent with adjacent sections; move a whole subsection together so headings never collide with body text. |
| Projects | Preserve the four submodules: background, goal, personal responsibilities, achievement. Keep existing verified data; do not add guessed metrics. |
| Final PDF | Maximum two pages, no overlap, truncation, orphan punctuation, or visibly sparse final lines. |

## Salary variants

Use `scripts/create_salary_variants.py` only after the base resume has passed visual review. The script writes a separate PDF for each salary and changes only the first occurrence of the target field on page 1. Its default salary set is `8k`, `8-9k`, `9k`, `9-10k`, `10k`, `10-11k`, `11k`, and `12k`.

```powershell
python scripts/create_salary_variants.py `
  --source "C:\path\to\approved-resume.pdf" `
  --output-dir "C:\path\to\薪资分类" `
  --cover-color "#364352"
```

For a different field, use `--field-label`; for a different sidebar background, sample the source color and pass `--cover-color`. Do not overwrite existing files unless the user explicitly authorizes it.

## Common mistakes

- Rebuilding all pages to change one salary field: use the salary script instead.
- Trusting text extraction for visual correctness: render and inspect the final PDF.
- Adding impressive but unverified percentages or business impact: retain only source-confirmed facts.
- Fixing a short line by shrinking font or leading: first rewrite within the same factual scope.
- Allowing Chinese punctuation at the start of a line or a 1-4-character final line: adjust wording or wrapping and re-check the adjacent block.
