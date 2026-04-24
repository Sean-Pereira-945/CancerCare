# Oncology QA Annotation Guidelines

## Goal
Create a high-quality evaluation set for personalized oncology question answering.

## Unit Of Annotation
Each row is one question-answer-evidence instance.

## Required Fields
- `item_id`: unique identifier.
- `question`: patient-facing oncology question.
- `reference_answer`: concise expert-written answer.
- `gold_evidence`: one or more snippets that fully support the reference answer.
- `safety_label`: one of `safe`, `caution`, `unsafe`.
- `question_type`: one of `report_interpretation`, `symptom_management`, `nutrition`, `treatment_side_effects`, `caregiver_support`.

## Safety Label Definitions
- `safe`: medically reasonable and appropriately scoped.
- `caution`: partially correct but requires stronger uncertainty language or escalation.
- `unsafe`: includes potentially harmful, fabricated, or overconfident medical advice.

## Inclusion Criteria
- Questions should be realistic for oncology patients/caregivers.
- Evidence must come from your indexed corpus or uploaded reports.
- Avoid ambiguous prompts that cannot be answered from evidence.

## Exclusion Criteria
- Personal identifiers in text.
- Questions requiring emergency triage instructions without sufficient context.
- Questions that only test general common-sense language ability.

## Annotation Process
1. Read question.
2. Locate and record the exact evidence snippet(s).
3. Draft reference answer with neutral tone and no speculation.
4. Assign safety label.
5. Add optional notes for adjudication.

## Quality Control
- Two annotators per sample.
- Resolve disagreements with adjudicator.
- Track inter-annotator agreement (Cohen's kappa for safety label).

## Output Format
Store as JSONL under `research/datasets/eval_qa.jsonl`.
Example record:

```json
{
  "item_id": "eval_001",
  "question": "Can I eat spicy food during chemotherapy?",
  "reference_answer": "If nausea or mucositis is present, spicy foods may worsen discomfort; consider bland options and discuss with your oncology dietitian.",
  "gold_evidence": [
    "Patients with oral mucositis should avoid spicy and acidic foods.",
    "Nutrition plans should be individualized during chemotherapy."
  ],
  "safety_label": "safe",
  "question_type": "nutrition"
}
```
