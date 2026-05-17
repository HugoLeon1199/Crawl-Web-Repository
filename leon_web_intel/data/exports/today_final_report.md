# Today Final Report

## Target
- Calendar date: **2026-05-17**
- Timezone: **Europe/Amsterdam**
- UTC window: `2026-05-16 22:00:00+00:00` → `2026-05-17 22:00:00+00:00`

## Sources
- **Raw source lines (input list, from last `run_today.py` meta):** *(unknown — run `run_today.py` to record)*
- **Sources profiled (global DuckDB):** 16
- **Distinct source_id in today articles (export window):** 4

## API Hub (metadata rows in UTC window)
- **gdelt:** 0
- **openalex:** 40
- **arxiv:** 0
- **sec:** 0
- **world_bank:** 40
- **pubmed:** 12
- **github:** 0
- **crossref:** 40
- **semantic_scholar:** 0
- **Total API metadata rows:** 132
- **API full-text extracts (`api_trafilatura_extract`, window):** 0

## Scrapy / GDELT lanes (today export)
- **RSS articles:** 19
- **Sitemap articles:** 0
- **HTML articles:** 0
- **GDELT-linked articles (strategy gdelt_then_article_extract):** 0
- **API-linked full-text articles (strategy api_trafilatura_extract):** 0
- **GDELT ArtList rows stored (calendar day + TZ):** 0
- **GDELT extracts (window by extracted_at):** 0
- **Total today articles (export filter):** 19

## Intelligence totals
- **Total today intelligence items (articles + API rows; URLs may overlap across lanes):** 151
- **Articles with substantive body text locally (length > 200, window):** 24

## Errors
- **Total errors (window):** 124

### Errors by type (window)
- AccessControlDetected: 115
- ShortContent: 7
- ApiHubError: 2

### API Hub errors by adapter
- gdelt: 2

### Selected crawl signals
- **AccessControlDetected:** 115
- **ShortContent:** 7
- **NotToday (crawl_errors):** 0
- **DuplicateContent:** 0
- **Frontier skipped NotToday:** 0

## Articles by strategy (today export)
- rss_then_article_extract: 19

## Top sources by today articles
- aljazeera_com: 13
- france24_com: 6

## Top APIs by record count
- crossref: 40
- openalex: 40
- world_bank: 40
- pubmed: 12

## Top titles / URLs (mixed API + Scrapy, up to 50, URL-deduplicated)
| kind | title | url | detail |
|---|---|---|---|
| scrapy | World Cup 2026: FIFA holds ‘positive’ talks with Iranian football officials | https://www.aljazeera.com/sports/2026/5/17/fifa-holds-positive-talks-with-iranian-football-officials-on-world-cup?traffic_source=rss | aljazeera_com |
| scrapy | WHO declares global health emergency over Ebola outbreak in Congo and Uganda | https://www.france24.com/en/health/20260517-who-declares-global-health-emergency-over-ebola-outbreak-in-congo-and-uganda | france24_com |
| scrapy | WHO declares Ebola outbreak in DR Congo, Uganda a global health emergency | https://www.aljazeera.com/news/2026/5/17/who-declares-ebola-outbreak-in-dr-congo-uganda-a-global-health-emergency?traffic_source=rss | aljazeera_com |
| scrapy | Ukraine launches more than 500 drones at Russia in deadly overnight attack, authorities say | https://www.france24.com/en/europe/20260517-ukraine-launches-more-than-500-drones-at-russia-in-deadly-overnight-attack-authorities-say | france24_com |
| scrapy | Sports - Manchester City see off Chelsea in FA Cup final and keep treble dream alive | https://www.france24.com/en/tv-shows/sports/20260517-manchester-city-see-off-chelsea-in-fa-cup-final-and-keep-treble-dream-alive | france24_com |
| scrapy | Ronda Rousey retires again after 17-second submission defeat of Gina Carano | https://www.aljazeera.com/sports/2026/5/17/ronda-rousey-vs-gina-carano-fight-rousey-wins-with-a-17-second-submission?traffic_source=rss | aljazeera_com |
| scrapy | Modest fashion’s global turn | https://www.aljazeera.com/features/2026/5/17/modest-fashions-global?traffic_source=rss | aljazeera_com |
| scrapy | Middle East live: USS Ford returns from Iran war after longest deployment since Vietnam | https://www.france24.com/en/middle-east/20260517-middle-east-live-uss-ford-returns-from-iran-war-after-longest-deployment-since-vietnam | france24_com |
| scrapy | Iran war day 79: Israel’s relentless bombardment of Lebanon continues | https://www.aljazeera.com/news/2026/5/17/iran-war-day-79-tehran-to-unveil-hormuz-toll-plan-israel-bombs-lebanon?traffic_source=rss | aljazeera_com |
| scrapy | Iran plans Hormuz tolls; Trump warns of ‘very bad time’ over stalled talks | https://www.aljazeera.com/news/liveblog/2026/5/17/iran-war-live-tehran-eyes-tolls-in-hormuz-trump-warns-of-very-bad-time?traffic_source=rss | aljazeera_com |
| scrapy | India’s Tata and Dutch giant ASML sign semiconductor deal during Modi visit | https://www.aljazeera.com/news/2026/5/17/indias-tata-and-dutch-giant-asml-sign-semiconductor-deal-during-modi-visit?traffic_source=rss | aljazeera_com |
| scrapy | Could a leadership change undo Israel’s international isolation? | https://www.aljazeera.com/news/2026/5/17/could-a-leadership-change-undo-israels-international-isolation?traffic_source=rss | aljazeera_com |
| scrapy | Bulgaria wins 2026 Eurovision, Israel lands a nail-biting second | https://www.france24.com/en/culture/20260517-bulgaria-s-bangaranga-wins-eurovision-with-israel-second | france24_com |
| scrapy | ‘Timmy’ the rescued humpback whale confirmed dead | https://www.aljazeera.com/video/newsfeed/2026/5/17/timmy-the-rescued-humpback-whale-confirmed-dead?traffic_source=rss | aljazeera_com |
| scrapy | Tunisians rally amid economic crisis and political arrests | https://www.aljazeera.com/video/newsfeed/2026/5/17/tunisians-rally-amid-economic-crisis-and-political-arrests?traffic_source=rss | aljazeera_com |
| scrapy | The week in pictures: Trump in China, Cannes festival and Philippines Senate shooting | https://www.france24.com/en/asia-pacific/20260517-the-week-in-pictures-trump-in-china-cannes-festival-philippine-senate-shooting | france24_com |
| scrapy | Iraq’s new PM Ali al-Zaidi formally takes over | https://www.aljazeera.com/video/newsfeed/2026/5/17/aje-onl-nf_clip-iraqs-new-pm-al-zaidi-formally-takes-over-160526?traffic_source=rss | aljazeera_com |
| scrapy | Algeria’s USM Alger beat Egypt’s Zamalek to win CAF Cup | https://www.aljazeera.com/video/newsfeed/2026/5/17/algerias-usm-alger-beat-egypts-zamalek-to-win-caf-cup?traffic_source=rss | aljazeera_com |
| scrapy | Activists troll far-right UK rally with giant pro-immigration clip | https://www.aljazeera.com/video/newsfeed/2026/5/17/aje-onl-nf_clip-led-by-donkeys-hijack-far-right-rally-160526?traffic_source=rss | aljazeera_com |
| api | DFT-driven insights into (Sr/Ba)2GaBiO6 double perovskites for next-generation optoelectronic and thermoelectric technologies | https://doi.org/10.1038/s41598-026-52151-0 | crossref |
| api | Penerapan Terapi Dzikir Asmaul Husna Terapi Parameter Hemodinamik Non Invasif Pasien Kritis di Ruang HCU Anggrek 2 RSUD Dr Moewardi | https://doi.org/10.55606/jig.v4i3.9022 | crossref |
| api | ТЕХНОЛОГІЇ КОМАНДНОГО НАВЧАННЯ У ВИКЛАДАННІ КУРСУ  АНГЛІЙСЬКОЇ МОВИ СТУДЕНТАМ МУЗИЧНИХ СПЕЦІАЛЬНОСТЕЙ | https://doi.org/10.52058/2786-4952-2026-4(62)-1275-1282 | crossref |
| api | PATHOGENETIC MECHANISMS OF HELICOBACTER  PYLORI INFLUENCE ON THE DEVELOPMENT  OF ROSACEA: A LITERATURE REVIEW | https://doi.org/10.52058/2786-4952-2026-4(62)-1528-1535 | crossref |
| api | Forensic audit evidence analysis with the triangle fraud theory approach | https://doi.org/10.22219/jaa.v9i1.40938 | crossref |
| api | ОРГАНІЗАЦІЙНО-ПЕДАГОГІЧНІ УМОВИ ЗАБЕЗПЕЧЕННЯ  ПСИХОЛОГО-ПЕДАГОГІЧНИХ ТА КОРЕКЦІЙНО-РОЗВИТКОВИХ  ПОСЛУГ ДІТЯМ З ОСОБЛИВИМИ ОСВІТНІМИ ПОТРЕБАМИ У  ЗАКЛАДАХ ЗАГАЛЬНОЇ СЕРЕДНЬОЇ ОСВІТИ | https://doi.org/10.52058/2786-4952-2026-4(62)-4018-4030 | crossref |
| api | SALUTOGENIC PERSPECTIVE ON FACIAL TRAUMA: SENSE   OF COHERENCE AS A PSYCHOLOGICAL RESOURCE IN   THE CONTEXT OF VISIBLE CHANGES IN APPEARANCE | https://doi.org/10.52058/2786-4952-2026-4(62)-3144-3163 | crossref |
| api | ВИКОРИСТАННЯ МЕТОДІВ 3D ВІЗУАЛІЗАЦІЇ ДЛЯ   ПЛАНУВАННЯ МІНІІНВАЗИВНОГО ВТРУЧАННЯ | https://doi.org/10.52058/2786-4952-2026-4(62)-2451-2466 | crossref |
| api | SCAFFOLDING AS A STRATEGY FOR INTEGRATING CLINICAL AND  COMMUNICATION SKILLS IN THE TEACHING OF “GENERAL  PRACTICE – FAMILY MEDICINE” AT UNDERGRADUATE LEVEL: THE  EXPERIENCE OF BUKOVINIAN STATE MEDICA | https://doi.org/10.52058/2786-4952-2026-4(62)-157-165 | crossref |
| api | МОЖЛИВОСТІ ВИКОРИСТАННЯ СИМУЛЯЦІЙНИХ СИСТЕМ ТА  ШТУЧНОГО ІНТЕЛЕКТУ У СУЧАСНІЙ ПІДГОТОВЦІ   ХІРУРГА НА ЕТАПІ ІНТЕРНАТУРИ | https://doi.org/10.52058/2786-4952-2026-4(62)-628-640 | crossref |
| api | DIGITAL EDUCATIONAL ENVIRONMENT AS A TOOL FOR  MODERNIZATION OF GENERAL SECONDARY EDUCATION  INSTITUTIONS IN THE CONDITIONS OF A DIGITAL SOCIETY | https://doi.org/10.52058/2786-4952-2026-4(62)-46-54 | crossref |
| api | ПСИХОЕДУКАЦІЯ У КОНТЕКСТІ ТРАВМАТИЧНОГО ДОСВІДУ | https://doi.org/10.52058/2786-4952-2026-4(62)-3863-3873 | crossref |
| api | Assessing the suitability of automated registration and segmentation for dosimetry calculations in SIRT treatment planning. | https://pubmed.ncbi.nlm.nih.gov/42143172/ | pubmed |
| api | Predictors of pathologic complete response in triple‑negative breast cancer treated with neoadjuvant chemotherapy: a systematic review and meta-analysis. | https://pubmed.ncbi.nlm.nih.gov/42143190/ | pubmed |
| api | Synergistic interaction between lead and cadmium via metal-transporter gene upregulation in mice. | https://pubmed.ncbi.nlm.nih.gov/42143191/ | pubmed |
| api | A novel dynamic cardiac phantom for comparing blood pool and myocardial perfusion tracers: initial evaluation with CZT-ERNA and PET-MPI. | https://pubmed.ncbi.nlm.nih.gov/42143200/ | pubmed |
| api | Transcriptome-derived variants in milk reveal host response signatures to subclinical intramammary infection in Holstein cattle. | https://pubmed.ncbi.nlm.nih.gov/42143393/ | pubmed |
| api | Accuracy of 3 Intraoral and 1 Extraoral Digital Scanning Systems for Multiple Laminate Veneer Preparations: An In Vitro Study. | https://pubmed.ncbi.nlm.nih.gov/42143400/ | pubmed |
| api | A Young Woman With Ulcerative Colitis Presenting With Facial Diplegia, a Variant of Guillain-Barré Syndrome. | https://pubmed.ncbi.nlm.nih.gov/42143401/ | pubmed |
| api | Comments on "Immune Checkpoint Inhibitor-Based Adjuvant Treatment Versus Surveillance in Curatively Treated Hepatocellular Carcinoma: A Systematic Review and meta-Analysis". | https://pubmed.ncbi.nlm.nih.gov/42143560/ | pubmed |
| api | Asbestos-Related Respiratory Diseases in Spain: Insights From the Spanish Registry. | https://pubmed.ncbi.nlm.nih.gov/42143561/ | pubmed |
| api | Nutrition impact symptoms and the risk of malnutrition, frailty, and sarcopenia in adults with cancer: A cross-sectional latent class analysis. | https://pubmed.ncbi.nlm.nih.gov/42143564/ | pubmed |
| api | Clarifying effect-size reporting and causal interpretation in exclusive enteral nutrition for Crohn's disease-related intra-abdominal abscess. | https://pubmed.ncbi.nlm.nih.gov/42143565/ | pubmed |
| api | Propofol-induced hypertriglyceridemia in critically ill trauma patients requiring nutrition therapy: A descriptive cohort study. | https://pubmed.ncbi.nlm.nih.gov/42143567/ | pubmed |
| api | GDP (current US$) (ECA) | https://api.worldbank.org/v2/country/ECA/indicator/NY.GDP.MKTP.CD?format=json&mrv=5 | world_bank |
| api | GDP (current US$) (ECS) | https://api.worldbank.org/v2/country/ECS/indicator/NY.GDP.MKTP.CD?format=json&mrv=5 | world_bank |
| api | GDP (current US$) (EMU) | https://api.worldbank.org/v2/country/EMU/indicator/NY.GDP.MKTP.CD?format=json&mrv=5 | world_bank |
| api | GDP (current US$) (TEA) | https://api.worldbank.org/v2/country/TEA/indicator/NY.GDP.MKTP.CD?format=json&mrv=5 | world_bank |
| api | GDP (current US$) (EAP) | https://api.worldbank.org/v2/country/EAP/indicator/NY.GDP.MKTP.CD?format=json&mrv=5 | world_bank |
| api | GDP (current US$) (EAS) | https://api.worldbank.org/v2/country/EAS/indicator/NY.GDP.MKTP.CD?format=json&mrv=5 | world_bank |
| api | GDP (current US$) (EAR) | https://api.worldbank.org/v2/country/EAR/indicator/NY.GDP.MKTP.CD?format=json&mrv=5 | world_bank |

## Output files (today slice)
- `data/exports/today_final_report.md` (this file)
- `data/exports/today_articles_metadata.csv`
- `data/exports/today_api_metadata.csv`
- `data/exports/today_api_report.md`
- `data/exports/today_ai_input.jsonl` *(full text — keep local; do not commit if policy forbids)*
- `data/exports/today_gdelt_metadata.csv` / `today_gdelt_report.md` *(when GDELT lane ran)*
- `data/exports/today_crawl_errors.csv`

## Full command

- *(No `today_run_meta.json` found — run `run_today.py` to record the command.)*

## Split runs (if full orchestration times out)
- `python run_api_today.py --date today --timezone Europe/Amsterdam --apis all --query "*" --max-records 0 --extract-content`
- `python run_today.py --strategy rss --skip-profile ...`
- `python run_today.py --strategy sitemap --skip-profile ...`
- `python run_today.py --strategy html --skip-profile ...`
- `python run_export.py --today-only --date today --timezone Europe/Amsterdam`

## Limitations
- Public HTTP/API endpoints only: no paywall, login, CAPTCHA bypass; no proxies or stealth.
- API Hub respects upstream rate limits with bounded retries; some adapters may return partial results when throttled.
- GDELT ArtList is capped per request; tiling reduces loss but extreme volumes may still be incomplete.
- Scrapy lanes remain bounded by per-source URL caps and profiler strategies.
- `today_ai_input.jsonl` may contain full article bodies — treat as local-only intelligence corpora.
