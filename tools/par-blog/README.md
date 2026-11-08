# PAR blog: public figures

The article is `_pages/blogs/prompt-aware-rubrics.html`; its index automatically
lists pages with `blog_article: true`.

All case artwork is original SVG schematic illustration. Instructions and example
verdicts are fictional teaching examples. No original presentation, video crop,
internal screenshot, raw score, confidence output, or original sample count is
stored in this directory or required by the build.

All experimental result data in `normalized-results.json` is already normalized.
Each comparison uses one common scale, preserving ratios and relative gains
subject to rounding. No claim is made that indices are raw accuracy rates or that
normalization preserves raw percentage-point differences. Comparison references
are stated in the article and charts.

`training-curves-normalized.csv` contains approximate digitized trends with both
training progress and accuracy normalized. Within each panel, the first
Augmentation V2 accuracy is the reference. The panels have separate scales.

Rebuild with Python, NumPy and Matplotlib:

```sh
python tools/par-blog/build_assets.py --out assets/images/par
```

The Gold-Rescue policy-shaping term is adapted from LUFFY
(arXiv:2504.14945, Section 3.2). Internal training hyperparameters are expressed
symbolically. The artifact-focused SP qualification is supplied by the author;
its complete internal text is not published.
