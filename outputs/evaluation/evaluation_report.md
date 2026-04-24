# Evaluation Snapshot

## Classification
- Accuracy: 0.9380
- Macro precision: 0.9263
- Macro recall: 0.9303
- Macro F1: 0.9250

## Summarization Review Design
- Review sheet scores summaries on coverage, specificity, and actionability using a 1-5 proxy rubric.
- Human reviewers can replace the proxy scores with analyst judgments during portfolio demos.

## Prioritization Checks
- Checks passed: 3 / 3
- Current checks validate ARR weighting, enterprise pain surfacing, and correlation with churn pressure.

## Known Limitations
- The classifier is trained on synthetic text, so production accuracy would likely be lower.
- Theme summaries are templated and should be paired with analyst review for executive use.
- Prioritization is decision support rather than an automatic roadmap allocator.