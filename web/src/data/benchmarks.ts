/** Published industry figures, each with a source and a date.
 *
 *  This file exists so that no number shown next to one of our results is
 *  invented. Where the industry has published a figure we cite it; where it has
 *  not, the `unverified` list below says so in as many words, and the interface
 *  labels the corresponding threshold a design choice rather than a standard.
 *
 *  Compiled July 2026. */

export interface Benchmark {
  label: string
  value: string
  source: string
  url: string
  year: string
  /** how our own number compares — shown beside it, never instead of it */
  note?: string
}

/* ---- straight-through processing ------------------------------------- */

export const stpBenchmarks: Benchmark[] = [
  {
    label: 'Applications eligible for accelerated underwriting',
    value: '59%',
    source: 'SOA Accelerated Underwriting Practices Survey (24 carriers)',
    url: 'https://www.soa.org/resources/research-reports/2023/acc-underwriting-practices-survey/',
    year: '2022 exp., published 2023',
  },
  {
    label: 'Of those eligible, share actually accelerated',
    value: '46%',
    source: 'SOA Accelerated Underwriting Practices Survey, Table 4-19',
    url: 'https://www.soa.org/resources/research-reports/2023/acc-underwriting-practices-survey/',
    year: '2021–2022',
  },
  {
    label: 'RGA-reinsured accelerated underwriting programmes',
    value: '40–50% average (range 10–70%)',
    source: 'RGA, Accelerated Underwriting Analysis',
    url: 'https://www.rgare.com/knowledge-center/article/accelerated-underwriting-analysis-examining-today-s-accelerated-underwriting-and-its-bright-future',
    year: 'undated',
  },
  {
    label: 'Cycle time to decision — accelerated vs traditional',
    value: '9 days vs 27 days',
    source: 'LIMRA',
    url: 'https://www.limra.com/en/newsroom/industry-trends/2020/life-insurers-look-to-make-the-underwriting-process-easier-for-customers/',
    year: '2020',
  },
]

/* ---- financial underwriting ------------------------------------------ */

export interface CoverageBand {
  age: string
  brighthouse: number
  pacificLife: number
  ours: number
}

/** Published income-replacement multiples from two carriers' underwriting
 *  guides, beside the table this system applies. */
export const coverageMultiples: CoverageBand[] = [
  { age: '20–30', brighthouse: 30, pacificLife: 30, ours: 25 },
  { age: '31–40', brighthouse: 30, pacificLife: 25, ours: 25 },
  { age: '41–45', brighthouse: 25, pacificLife: 20, ours: 20 },
  { age: '46–50', brighthouse: 20, pacificLife: 20, ours: 20 },
  { age: '51–55', brighthouse: 20, pacificLife: 15, ours: 15 },
  { age: '56–60', brighthouse: 15, pacificLife: 15, ours: 15 },
  { age: '61–65', brighthouse: 10, pacificLife: 10, ours: 10 },
]

export const coverageSources: Benchmark[] = [
  {
    label: 'Brighthouse Financial — Term Life Underwriting Guide',
    value: '30× under 40 → 10× at 61–70',
    source: 'Brighthouse Financial',
    url: 'https://pinneyinsurance.com/underwriting-docs/Brighthouse-UW-Guide.pdf',
    year: 'current guide',
  },
  {
    label: 'Pacific Life — Financial Underwriting (MKTG-BRK-49B)',
    value: '30× at 20–30 → 5× at 66–75',
    source: 'Pacific Life',
    url: 'https://www.champion-agency.com/wp-content/uploads/2020/05/PL_Financial_UW.pdf',
    year: 'current guide',
  },
]

/* ---- non-disclosure --------------------------------------------------- */

export const disclosureBenchmarks: Benchmark[] = [
  {
    label: 'Applicants who deny tobacco but test cotinine-positive',
    value: '≈4% of all applicants',
    source: 'Clinical Reference Laboratory — 6.7M samples, 2014–2021',
    url: 'https://www.crlcorp.com/insurer-services-blog/cotinine-levels-and-smoker-misrepresentation-over-time',
    year: 'published 2024',
  },
  {
    label: 'Share of actual tobacco users who do not disclose',
    value: 'approaching 50%',
    source: 'Clinical Reference Laboratory',
    url: 'https://www.crlcorp.com/insurer-services-blog/cotinine-levels-and-smoker-misrepresentation-over-time',
    year: 'published 2024',
  },
  {
    label: 'Smoker misrepresentation found in random holdout audits',
    value: '1–3%',
    source: 'SOA Accelerated Underwriting Practices Survey, Tables 4-44/4-45',
    url: 'https://www.soa.org/resources/research-reports/2023/acc-underwriting-practices-survey/',
    year: '2019–2022',
  },
]

/* ---- model discrimination -------------------------------------------- */

export const aucBenchmarks: Benchmark[] = [
  {
    label: 'Life insurance applicants, ≥25% extra mortality (n≈15,094)',
    value: '0.708 – 0.743',
    source: 'Added Value of Medical Testing in Underwriting Life Insurance, PLoS One',
    url: 'https://pmc.ncbi.nlm.nih.gov/articles/PMC4696800/',
    year: '2015',
    note: 'the closest true peer — a real applicant population',
  },
  {
    label: 'UK Biobank, 5-year all-cause mortality, self-reported predictors',
    value: '0.80 men / 0.79 women',
    source: 'Ganna & Ingelsson, The Lancet',
    url: 'https://www.thelancet.com/journals/lancet/article/PIIS0140-6736(15)60175-1/fulltext',
    year: '2015',
  },
  {
    label: 'UK Biobank, premature all-cause mortality, machine learning',
    value: '0.783 RF / 0.790 deep learning',
    source: 'Weng et al., PLoS One',
    url: 'https://www.ncbi.nlm.nih.gov/pmc/articles/PMC6436798/',
    year: '2019',
  },
  {
    label: 'Insurance risk prediction, XGBoost',
    value: '0.86',
    source: 'Complex & Intelligent Systems, Springer',
    url: 'https://link.springer.com/article/10.1007/s40747-018-0072-1',
    year: '2018',
  },
]

/* ---- governance -------------------------------------------------------- */

export interface Obligation {
  regime: string
  status: string
  url: string
  requires: string[]
  /** what this build actually does about it — honest, including "nothing yet" */
  position: string
  met: 'partial' | 'none' | 'design'
}

export const obligations: Obligation[] = [
  {
    regime: 'NAIC Model Bulletin — Use of AI Systems by Insurers',
    status: 'Adopted Dec 2023; in force in roughly half of US jurisdictions by 2026',
    url: 'https://content.naic.org/sites/default/files/inline-files/2023-12-4%20Model%20Bulletin_Adopted_0.pdf',
    requires: [
      'A written AI Systems Program with board-level accountability',
      'Model inventory and lifecycle documentation',
      'Methods to detect errors, drift and unfair discrimination',
      'Validation against unseen and post-implementation data',
      'Consumer notice that AI systems are in use',
    ],
    position:
      'The rule layer is fully traceable and every decision carries its reasons, the model card below is the development record, and thresholds are validated on a held-out half. There is no board-level programme, no model inventory and no drift monitoring — those are organisational artefacts a prototype cannot produce.',
    met: 'partial',
  },
  {
    regime: 'Colorado Reg 10-1-1 — Governance for Life Insurers using ECDIS',
    status: 'Adopted Sept 2023, effective Nov 2023; governance framework due Dec 2024',
    url: 'https://doi.colorado.gov/announcements/notice-of-adoption-new-regulation-10-1-1-governance-and-risk-management-framework',
    requires: [
      'Governance framework covering external consumer data and predictive models',
      'Annual attestation to the Division',
      'Quantitative testing for proxy discrimination — see status note',
    ],
    position:
      'Not claimed. The quantitative testing regulation that would specify the BIFSG proxy method remains a draft, and Colorado waived the testing requirement for the 2024 and 2025 reports. This build audits outcomes and error rates by age band and sex only — it holds no race or ethnicity proxy, so it does not perform the test Colorado has drafted.',
    met: 'none',
  },
  {
    regime: 'EU AI Act — Annex III 5(c)',
    status: 'Life and health insurance risk assessment and pricing is high-risk; obligations apply from 2 Aug 2026',
    url: 'https://artificialintelligenceact.eu/annex/3/',
    requires: [
      'Risk management system and data governance',
      'Technical documentation and automatic logging',
      'Human oversight built into the system',
      'Accuracy, robustness and cybersecurity',
    ],
    position:
      'Human oversight is the design centre, not an add-on: every referral routes to a named underwriter and no case reaches a customer without one. Logging, the risk management system and a conformity assessment do not exist.',
    met: 'design',
  },
]

/** Stated plainly, because a production-grade claim rests on knowing the gaps. */
export const unverified: string[] = [
  'No published life-insurance standard exists for a premium-to-income cap or a debt-service ratio. Both thresholds in this system are design choices, not industry norms.',
  'No authoritative cost per policy issued, or underwriting expense ratio, could be sourced for US life insurance. This build makes no cost-saving claim.',
  'No published rate exists for income misstatement on life applications, so the injection rate for that conflict is a modelling assumption.',
  'No regulator publishes a required fairness test statistic for life models. NAIC and EIOPA require that you test, not how.',
]
