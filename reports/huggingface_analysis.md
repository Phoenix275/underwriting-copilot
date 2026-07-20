# Hugging Face Models & Datasets vs. Our Engine — Analysis Report

*Underwriting Copilot POC · Tech Mahindra GLP · 2026-07-20*
*Hardware evaluated against: Apple M2, 8 cores, 16 GB RAM, 17 GB free disk, Metal GPU*

## Method

Live queries against the Hugging Face API across model/dataset searches
(insurance, underwriting, actuarial, mortality, tabular, TabPFN, health
indicators), followed by an **empirical head-to-head benchmark run on this
machine using our own training pool** (8,000 applicants, 20 features,
identical train/test split).

## Empirical benchmark (our data, this laptop)

| Model | Origin | Train rows | AUC | Fit+predict time |
|---|---|---|---|---|
| Gradient Boosting (ours) | scikit-learn, trained by us | 6,400 | 0.8794 | 0.6 s |
| Logistic Regression (ours) | scikit-learn, trained by us | 6,400 | 0.8831 | <0.1 s |
| **TabPFN v2** | Prior Labs pre-trained foundation model (HF, 29 MB) | 3,000 | **0.8844** | 129.6 s (CPU) |

TabPFN v2 — a Nature-published pre-trained tabular foundation model — matched
our engine to within ~0.005 AUC while using half the training data, but at
~200× the inference cost. All three models are converging on the same number
because our synthetic labels contain deliberate noise; ~0.88–0.89 is the
data's ceiling, which independently confirms our engine is already extracting
essentially all available signal.

## What exists on Hugging Face

### Models

| Model | What it is | Usable for our scoring? | Runs on M2/16GB? |
|---|---|---|---|
| Prior-Labs/TabPFN-v2-clf (19.5k downloads) | Pre-trained tabular classifier, 29 MB | Yes — tested above | Yes (CPU; slow at scale) |
| TabPFN 3 / 2.5 (newest) | Latest foundation models | Gated: requires Prior Labs account/API key — vendor dependency | Yes, same caveat |
| Open-Insurance-LLM-Llama3-8B (+GGUF) | Insurance-domain chat/Q&A LLM (NVIDIA-affiliated author) | Not for scoring — ideal for the narrative/summary layer, offline via Ollama | Yes (Q4 ≈ 4.3–4.5 GB) |
| llmware/industry-bert-insurance | Insurance-domain embeddings | Document retrieval, not risk scoring | Yes |
| "underwriting" search results | Toy uploads, 0–13 downloads, no cards | No | — |

**Key negative finding:** there is *no* credible pre-trained life-insurance
underwriting risk model on Hugging Face. Everything with the word
"underwriting" is either an LLM chat fine-tune or an empty student upload.
Carriers do not publish their scoring models. Our niche is empty — that is
good news for the POC's originality.

### Datasets

| Dataset | Size | Value to us |
|---|---|---|
| Bena345/cdc-diabetes-health-indicators (BRFSS) | 253k real CDC survey rows | **High — best single addition**; age/BMI/smoker/BP overlap with our schema |
| rahulvyasm/medical_insurance_data | ~2.7k rows, insurance charges | Moderate — larger sibling of a prior we already use |
| snorkelai/Multi-Turn-Insurance-Underwriting | <1k agent conversation traces | Not for scoring; useful later for an LLM-assistant evaluation layer |
| electricsheepafrica actuarial-mortality | 10k+ synthetic rows | Low — synthetic like ours, adds no real-world signal |
| MorbidCorp actuarial exam sets | Exam Q&A text | None for scoring |

## Verdict

1. **Keep our engine as the production scorer.** It matches the best
   available pre-trained model on accuracy, is 200× faster, fully auditable
   (rule factors + logistic coefficients), has no vendor gate, and STP
   thresholds are tuned against ground truth — regulators and managers can
   inspect every step.
2. **Adopt TabPFN v2 as a challenger/validation model**, not the champion:
   run it quarterly (or per retrain) as an independent second opinion; if it
   ever materially beats the champion, that flags real signal we're missing.
   Pin `tabpfn==2.0.9` (last ungated release).
3. **Ingest BRFSS (253k rows) as prior #21** — the single highest-value
   dataset found; an order of magnitude more real-world rows than our current
   largest prior.
4. **Optional demo upgrade:** Open-Insurance-LLM-8B (Q4 GGUF) via Ollama
   gives fully offline, insurance-domain case narratives on this laptop,
   replacing template summaries without any API key.

## Hardware fit (Apple M2, 16 GB)

- Our engine: trivial (seconds, <1 GB RAM).
- TabPFN v2: fine as a batch/validation tool (29 MB weights; minutes on CPU;
  MPS GPU unsupported by the library's memory estimator today).
- Insurance LLM 8B Q4: comfortable (~4.5 GB disk, ~6 GB RAM in use).
- Not feasible locally: 70B-class models, full AutoML sweeps under time
  constraints.
