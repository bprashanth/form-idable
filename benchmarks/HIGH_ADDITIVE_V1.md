# Additive subscription High — release evidence

The current release evidence is recorded stage by stage in
[`chronology/014_additive_subscription_high_all_form_gate.md`](../chronology/014_additive_subscription_high_all_form_gate.md).

Headline local gate: 14/14 PDFs, 68/68 pages, zero artifact errors; micro
semantic F1 0.887 Low to 0.910 High; precision 0.854 to 0.917; recall 0.924 to
0.904; 1,854/21,006 red review cells (8.83%); 36 orange ecology findings.

`HIGH_SWEEP_V1.md` remains the historical Gemini/OpenRouter experiment. Its
provider account is depleted and that image is not the current candidate.

Reproduce or inspect with:

```console
uv run --with openpyxl --with pillow --with pymupdf \
  python benchmarks/wide/validate_high_sweep.py \
  --root benchmarks/high_runs/additive_v1
```

Raw model evidence is gitignored under `benchmarks/high_runs/additive_v1/`.
Browser screenshots are under `benchmarks/high_visuals/additive-v1/`.

