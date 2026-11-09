# PAR blog figures

The article is `_pages/blogs/prompt-aware-rubrics.html`; the Blogs index lists
pages with `blog_article: true`.

Experimental values in `results.json` are reported at their original scales.
Benchmark names remain anonymized as Bench1–Bench5. Production usability combines
strictly usable and tolerable data, with both components shown separately.
The external precision/recall comparison uses one version-comparison snapshot;
unreported accuracy and F1 are left blank.

All case artwork is original SVG schematic illustration. Instructions and example
verdicts are fictional teaching examples. No original video frames, project
screenshots, original case confidences, or private source PDF are included.

`training-curves-digitized.csv` approximates the original training plots through
color-based digitization; it is not raw experiment logging. Accuracy is stored as
a fraction and plotted as a percentage against the original step axis.

Rebuild with Python, NumPy and Matplotlib:

```sh
python tools/par-blog/build_assets.py --out assets/images/par
```

Gold-Rescue policy shaping is adapted from LUFFY (arXiv:2504.14945, Section 3.2).
The artifact-focused SP qualification is supplied by the author; its full internal
text is not published.
