# Today Final Report

## Target
- Calendar date: **2026-05-18**
- Timezone: **Europe/Amsterdam**
- UTC window: `2026-05-17 22:00:00+00:00` → `2026-05-18 22:00:00+00:00`

## Sources
- **Raw source lines (input list, from last `run_today.py` meta):** 200
- **Sources profiled (global DuckDB):** 198
- **Distinct source_id in today articles (export window):** 218

## API Hub (metadata rows in UTC window)
- **gdelt:** 2270
- **openalex:** 102
- **arxiv:** 0
- **sec:** 0
- **world_bank:** 266
- **pubmed:** 100
- **github:** 100
- **crossref:** 200
- **semantic_scholar:** 0
- **Total API metadata rows:** 3038
- **API full-text extracts (`api_trafilatura_extract`, window):** 355

## Scrapy / GDELT lanes (today export)
- **RSS articles:** 356
- **Sitemap articles:** 426
- **HTML articles:** 137
- **GDELT-linked articles (strategy gdelt_then_article_extract):** 0
- **API-linked full-text articles (strategy api_trafilatura_extract):** 285
- **GDELT ArtList rows stored (calendar day + TZ):** 0
- **GDELT extracts (window by extracted_at):** 0
- **Total today articles (export filter):** 1204

## Intelligence totals
- **Total today intelligence items (articles + API rows; URLs may overlap across lanes):** 4242
- **Articles with substantive body text locally (length > 200, window):** 1480

## Errors
- **Total errors (window):** 2978

### Errors by type (window)
- AccessControlDetected: 1343
- NotToday: 1020
- FetchError: 345
- HttpError: 173
- ShortContent: 97

### API Hub errors by adapter
- None


### Selected crawl signals
- **AccessControlDetected:** 1343
- **ShortContent:** 97
- **NotToday (crawl_errors):** 1020
- **DuplicateContent:** 0
- **Frontier skipped NotToday:** 566

## Articles by strategy (today export)
- sitemap_then_article_extract: 426
- rss_then_article_extract: 356
- api_trafilatura_extract: 285
- html_then_trafilatura: 137

## Top sources by today articles
- businesstimes_com_sg: 56
- thehindu_com: 56
- koreaherald_com: 52
- vietnamplus_vn: 52
- europarl_europa_eu: 50
- kompas_com: 49
- cna_com_tw: 47
- economictimes_indiatimes_com: 47
- livemint_com: 47
- timesofindia_indiatimes_com: 45

## Top APIs by record count
- gdelt: 2270
- world_bank: 266
- crossref: 200
- openalex: 102
- github: 100
- pubmed: 100

## Top titles / URLs (mixed API + Scrapy, up to 50, URL-deduplicated)
| kind | title | url | detail |
|---|---|---|---|
| scrapy | ����¼����ֱǩ������ת�ࡱ����������ְ�����辯�� - ��Ʒ�� | https://www.xxrb.com.cn/html/2026/mph_0518/44831.html | gdelt_xxrb_com_cn |
| scrapy | �й���Ȳ������ι��ʱ������̹��� - ������������ | https://www.xxrb.com.cn/html/2026/lvyou_0518/44835.html | gdelt_xxrb_com_cn |
| scrapy | 인크루트, 공고 매칭 넘어 ‘합격 코칭’ 강화…개인 구직자 공략 | https://zdnet.co.kr/view/?no=20260518090804 | gdelt_zdnet_co_kr |
| scrapy | 스토킹·가정폭력 1년 새 23% 급증... 피해자 5만 명 공동 관리 나선다 | https://www.insight.co.kr/news/554518 | gdelt_insight_co_kr |
| scrapy | 삼성 노사, 오늘 2차 사후조정···역대 긴급조정권 어땠나 - 뉴스웨이 | https://newsway.co.kr/news/view?ud=2026051721531911529 | gdelt_newsway_co_kr |
| scrapy | 노타, AI 최적화 기술로 1분기 매출 53배 '껑충' | https://zdnet.co.kr/view/?no=20260518102749 | gdelt_zdnet_co_kr |
| scrapy | 규모 넘어 '가치'로 승부, 中 자동차 산업 체질 변화 '뚜렷' | http://kr.xinhuanet.com/20260518/5dd991d410054374aaed582dd0ff4b37/c.html | gdelt_kr_xinhuanet_com |
| scrapy | 고유가 지원금 맞춰 할인 확대…이마트24, PB·간편식 40% 페이백 | https://zdnet.co.kr/view/?no=20260518102111 | gdelt_zdnet_co_kr |
| scrapy | 黃天賜有感職棒「沒這麼簡單」 增重提升身體素質 \| 運動 \| 中央社 CNA | https://www.cna.com.tw/news/aspt/202605180190.aspx | cna_com_tw |
| scrapy | 饶平县纪委监委：联动监督助力农文旅融合发展-潮州新闻网-潮州日报官方网站 | https://www.chaozhoudaily.com/content/202605/18/c26059061.html | gdelt_chaozhoudaily_com |
| scrapy | 饮食之道，照见文明交融之妙 | http://www.dangjian.cn/whsb/2026/05/18/detail_202605187832763.html | gdelt_dangjian_cn |
| scrapy | 风雨之中有人遮护 向阳之处携手奔赴 - 社会 | http://fjnews.fjsen.com/2026-05/18/content_32186411.htm | gdelt_fjnews_fjsen_com |
| scrapy | 預防性處理毒駕 內政部盼修法限制吸毒紀錄者持駕照 \| 政治 \| 中央社 CNA | https://www.cna.com.tw/news/aipl/202605180090.aspx | cna_com_tw |
| scrapy | 韓國三星大罷工倒數3天 政府急介入勞資重啟談判 \| 國際 \| 中央社 CNA | https://www.cna.com.tw:443/news/aopl/202605180072.aspx | gdelt_cna_com_tw_443 |
| scrapy | 非遗古彩戏法与戏剧深度融合 岳秀清吴刚同台“变戏法” | https://culture.qianlong.com/2026/0518/8669296.shtml | gdelt_culture_qianlong_com |
| scrapy | 雷军马斯克合影引揶揄：小米“话题营销”过度，“人设IP”或临危机 | https://www.itbear.com.cn/html/2026-05/1345282.html | gdelt_itbear_com_cn |
| scrapy | 零食赛道新动向：良品铺子入局社区超市，卖菜背后藏着怎样的商业逻辑？ | https://www.itbear.com.cn/html/2026-05/1345011.html | gdelt_itbear_com_cn |
| scrapy | 雲林優質農漁產品 有望納入北市營養午餐菜單 \| 地方 \| 中央社 CNA | https://www.cna.com.tw/news/aloc/202605180160.aspx | cna_com_tw |
| scrapy | 陕西印发2026年全面依法治省工作要点 部署27项重点任务 | https://news.hsw.cn/system/2026/0518/1930232.shtml | gdelt_news_hsw_cn |
| scrapy | 陕晋甘三省制定18项年度重点任务推进关中平原城市群建设 | https://news.hsw.cn/system/2026/0518/1930279.shtml | gdelt_news_hsw_cn |
| scrapy | 陕晋甘三省制定18项年度重点任务推进关中平原城市群建设 | https://news.hsw.cn/system/2026/0518/1930228.shtml | gdelt_news_hsw_cn |
| scrapy | 阿北擁1470萬想留遺產給兒 卻遭怒吼「一毛錢都不要」背後真相太殘酷 - 自由財經 | https://ec.ltn.com.tw/article/breakingnews/5440772 | gdelt_ec_ltn_com_tw |
| scrapy | 金融時報：夏季高峰將至 伊朗能源危機進入新階段 \| 國際 \| 中央社 CNA | https://www.cna.com.tw/news/aopl/202605180050.aspx | gdelt_cna_com_tw |
| scrapy | 選務人力招募困難 竹縣盼中央核予補休2天 \| 政治 \| 中央社 CNA | https://www.cna.com.tw/news/aipl/202605180187.aspx | cna_com_tw |
| scrapy | 进出口同比增长14.9%！国家统计局公布1—4月经济数据 | https://news.southcn.com/node_812903b83a/c7d97a22f8.shtml | gdelt_news_southcn_com |
| scrapy | 跨行金融資訊系統 | https://www.cbc.gov.tw/tw/lp-393-1.html | cbc_gov_tw |
| scrapy | 越来越多年轻人挑起科技创新大梁 | http://www.tynews.com.cn/system/2026/05/18/031022236.shtml | gdelt_tynews_com_cn |
| scrapy | 超频破界 次元出圈 华硕主板竞耀2026 ROG DAY | https://www.itbear.com.cn/html/2026-05/1345168.html | gdelt_itbear_com_cn |
| scrapy | 超加工食品增加心脏病和早逝风险 | https://tech.gmw.cn/2026-05/18/content_38770079.htm | gdelt_tech_gmw_cn |
| scrapy | 贾跃亭上任CEO仅一周，FF再获2500万美元融资，两月累计融资7000万美元 | https://www.itbear.com.cn/html/2026-05/1345063.html | gdelt_itbear_com_cn |
| scrapy | 貨幣政策與支付系統 | https://www.cbc.gov.tw/tw/np-1037-1.html | cbc_gov_tw |
| scrapy | 貨幣政策簡介 | https://www.cbc.gov.tw/tw/np-2170-1.html | cbc_gov_tw |
| scrapy | 貨幣政策工具 | https://www.cbc.gov.tw/tw/np-1000-1.html | cbc_gov_tw |
| scrapy | 財部：4月新生兒普發現金1萬元 領取期限剩5天 \| 生活 \| 中央社 CNA | https://www.cna.com.tw/news/ahel/202605180091.aspx | cna_com_tw |
| scrapy | 谁是真正的“深蓝”猎手？ | https://hznews.hangzhou.com.cn/jingji/content/2026-05/18/content_9224232.htm | gdelt_hznews_hangzhou_com_cn |
| scrapy | 谁在贩卖你的个人信息？ | http://news.cyol.com/gb/articles/2026-05/18/content_779m9JHe3M.html | gdelt_news_cyol_com |
| scrapy | 让自信点燃创新：重视博士生教育的肯定性评价 | http://news.cyol.com/gb/articles/2026-05/18/content_xaogO6sVxP.html | gdelt_news_cyol_com |
| scrapy | 警政署區域聯防淨化宗教活動 查緝12組織、68嫌 \| 社會 \| 中央社 CNA | https://www.cna.com.tw/news/asoc/202605180137.aspx | cna_com_tw |
| scrapy | 諾貝爾文學獎得主古納：殖民遺緒仍影響當代社會【專訪】 \| 國際 \| 中央社 CNA | https://www.cna.com.tw/news/aopl/202605180027.aspx | gdelt_cna_com_tw |
| scrapy | 許安進當選中華羽協理事長 深化基層羽球運動 \| 運動 \| 中央社 CNA | https://www.cna.com.tw/news/aspt/202605180175.aspx | cna_com_tw |
| scrapy | 观海潮评丨坚决摒弃“混”的心态-烟台社会-水母网 | https://news.shm.com.cn/2026-05/18/content_5487785.htm | gdelt_news_shm_com_cn |
| scrapy | 被日本女性追捧的麻辣烫，真能暖宫祛湿当药膳？ | https://health.ycwb.com/2026-05/17/content_54123812.htm | gdelt_health_ycwb_com |
| scrapy | 行動工商憑證正式上線 經部估1年內換發逾18萬張 \| 產經 \| 中央社 CNA | https://www.cna.com.tw/news/afe/202605180188.aspx | cna_com_tw |
| scrapy | 行业ETF风向标丨中韩半导体ETF华泰柏瑞（513310）成交近90亿元，3只数字经济ETF半日涨幅超2% | https://www.nbd.com.cn/articles/2026-05-18/4396613.html | gdelt_nbd_com_cn |
| scrapy | 苹果“瑕疵芯片”再利用：以分级策略打造低价爆款，拓展利润空间 | https://www.itbear.com.cn/html/2026-05/1345194.html | gdelt_itbear_com_cn |
| scrapy | 苹果6月WWDC将推独立Siri应用，隐私保护成核心，或设聊天记录自动删功能 | https://www.itbear.com.cn/html/2026-05/1345088.html | gdelt_itbear_com_cn |
| scrapy | 苏州以一流营商环境融入全球经济循环 _新华网江苏频道 | http://www.js.xinhuanet.com/20260518/ad647fe58ce34fb6a021250924402e73/c.html | gdelt_js_xinhuanet_com |
| scrapy | 花蓮縣總預算爭議延宕半年落幕 縣府：加速行政 \| 政治 \| 中央社 CNA | https://www.cna.com.tw/news/aipl/202605180172.aspx | cna_com_tw |
| scrapy | 艾司摩爾攜手塔塔電子 建印度首座晶圓廠 - 自由財經 | https://ec.ltn.com.tw/article/breakingnews/5440722 | gdelt_ec_ltn_com_tw |
| scrapy | 自由廣場》預算刪成負數 「馬式」監督搞垮國防？！ - 自由評論網 | https://talk.ltn.com.tw/article/paper/1755212 | gdelt_talk_ltn_com_tw |

## Output files (today slice)
- `data/exports/today_final_report.md` (this file)
- `data/exports/today_articles_metadata.csv`
- `data/exports/today_api_metadata.csv`
- `data/exports/today_api_report.md`
- `data/exports/today_ai_input.jsonl` *(full text — keep local; do not commit if policy forbids)*
- `data/exports/today_gdelt_metadata.csv` / `today_gdelt_report.md` *(when GDELT lane ran)*
- `data/exports/today_crawl_errors.csv`

## Full command

- `python run_today.py --skip-profile --date today --timezone Europe/Amsterdam`

## Run ID

- `6f1bc77b-0f8b-4141-9060-7c4a4b1206f1`


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
