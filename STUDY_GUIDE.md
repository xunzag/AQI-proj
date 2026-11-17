# Study guide

This file is for me, to prepare for the admission interview. It follows the project's checkpoints. Each one has 5 key points and 2 questions; try to answer the questions out loud before reading the answers.

---

## Checkpoint 1: Data (notebooks 01–02)

**Key points**
1. The data is official: ARPA Lombardia's monitoring network, published by Regione Lombardia on dati.lombardia.it (Socrata API). I stitched three archive datasets (2010–17, 2018–25, current year) using non-overlapping date windows.
2. I used 10 sensors at 5 Milan stations that ran for the whole 2015–2026 period. Stations that opened or closed mid-way were excluded, because they would create fake jumps in the city average.
3. PM10 and PM2.5 are **daily** values (24-hour filter samples); NO2 is **hourly**. So hour-of-day analysis is only possible for NO2.
4. ARPA marks invalid values with `stato = NA` and the value `-9999` (2.6–3.5% of rows). I turned them into missing values and never filled gaps in. I also found a pandas pitfall: by default `read_csv` turns the text "NA" into a missing value, which hid the flag.
5. NO2 timestamps mark the *end* of the hour, so I shifted them back one hour. A day needs ≥ 18 valid hours (the EU 75% rule), and the city average needs ≥ 2 stations.

**Questions**
1. *Why not just delete the `-9999` rows?*
   Leaving `-9999` in would wreck every average (one value can pull a monthly mean far below zero). Deleting the rows hides the gaps, so you can no longer see or count missing data. Turning them into NaN keeps the gap visible, and each later step decides explicitly how to handle it (e.g. the 18-hour rule).
2. *Why require at least 2 stations for the city average?*
   Stations have different levels (traffic vs background sites). If one station is down and the average uses only the other, the "city" value jumps for a reason that has nothing to do with the air. Requiring 2 keeps the meaning of "Milan" stable.

---

## Checkpoint 2: Trends and patterns (notebook 03)

**Key points**
1. From 2015 to 2025: NO2 −45% (58.5 → 32.1 µg/m³), PM10 −36%, PM2.5 −35%. Theil–Sen slopes: NO2 −2.6 µg/m³ per year, PM about −1.1 to −1.3. Kendall p < 0.01 for all.
2. Still far above WHO 2021 guidelines in 2025: PM10 1.7×, PM2.5 3.9×, NO2 3.2×.
3. Winter is much worse: January PM2.5 is 3.5× the cleanest summer month. The causes are Po Valley geography, temperature inversions and heating.
4. NO2 is 19% below its weekly mean on Sundays and has a weekday morning peak: a traffic signature. PM's weekly cycle is weaker because much of it is *secondary*.
5. EU PM10 limit (50 µg/m³, max 35 days/year per station): days above it fell from 91–101 per station (2015) to 21–36 (2025), but there was never a year in which all stations complied.

**Questions**
1. *Why Theil–Sen instead of ordinary linear regression for the trend?*
   With only 11 annual points, one odd year (e.g. 2020) can pull a least-squares line a lot. Theil–Sen uses the median of all pairwise slopes, so it is robust to outliers.
2. *Why does NO2 have a stronger weekly cycle than PM2.5?*
   NO2 is emitted directly by combustion, mainly traffic, which drops on Sundays. A large part of PM2.5 forms in the air over days (from ammonia, NOx and other gases), or comes from heating and agriculture, which do not follow the working week.

---

## Checkpoint 3: Lockdown (notebook 04)

**Key points**
1. Window: 9 March – 3 May 2020 (national lockdown "Phase 1"), compared with the same dates in other years.
2. Three comparisons, each stricter than the last: naive (vs 2015–19 average), trend-adjusted, and a ratio to the same year's Jan–Feb (a difference-in-differences idea), plus a placebo test over all 11 years.
3. NO2: −43% naive, −29% trend-adjusted, −40% ratio method. 2020 ranks 1st of 11 years (the next most extreme is −22%). All 5 stations show 37–49% drops.
4. PM10 and PM2.5: lower than average naively (−13%, −20%), but not unusual after adjustment. 2019 and 2024 had similar "drops" without any lockdown.
5. My hypothesis that the morning rush-hour peak would collapse was only partly right: the morning peak fell about 30% (like the night), while the biggest drop was in the afternoon (−57%).

**Questions**
1. *Why isn't "2020 vs the 2015–19 average" enough?*
   Pollution falls every year anyway (the trend), and every year's weather is different. A naive comparison credits the lockdown with the trend and with weather luck. The trend adjustment and the ratio to the same year's winter remove those year-level effects, and the placebo test shows how big "effects" are in normal years.
2. *Did the lockdown cause the NO2 drop? Can you say that?*
   It is very likely, but not proven. 2020 is far outside the normal range in a placebo test, and the drop happened right after early March while January–February 2020 was normal. But I didn't include weather, and I can't observe the same spring without a lockdown. So I say "strong evidence consistent with a lockdown effect", not "proof".

---

## Checkpoint 4: Forecast (notebook 05)

**Key points**
1. Task: at the end of day *t*, predict city PM10 on day *t + 1*. Features use only data up to day *t*; a unit test checks that changing future values does not change past features.
2. Chronological split: train 2015–2022, select with calendar-year cross-validation plus 2023, test once on 2024–2025, extra check on 2026.
3. Baseline "tomorrow = today": MAE 7.91 µg/m³. Selected model (linear regression): 7.21, which is 8.9% better (bootstrap 95% CI for the gain: 0.33–1.09).
4. LightGBM was about as good as linear regression (within 0.15 µg/m³), so the simpler model is fine here.
5. Biggest limitation: no weather data. Cold-season errors are about 2.4× warm-season errors, and forecasts lag sudden spikes by about a day.

**Questions**
1. *Why not a random train/test split?*
   Neighbouring days are very similar. With a random split the model would see 14 January in training and be tested on 15 January, which is nearly the same answer. That overstates accuracy. A real forecaster only knows the past, so the test must come after the training data.
2. *Why is the naive baseline so important?*
   Without it, "MAE 7.2" means nothing. Pollution persists for days, so "tomorrow = today" is already decent. A model is only useful if it beats that, and the comparison shows the real added value (about 9%).

---

## Glossary (plain language)

- **µg/m³:** micrograms of pollutant per cubic metre of air.
- **PM10 / PM2.5:** particles smaller than 10 / 2.5 micrometres. PM2.5 is part of PM10 and goes deeper into the lungs.
- **NO2:** nitrogen dioxide, mostly from combustion (especially diesel traffic).
- **Secondary PM:** particles formed in the air from gases (e.g. ammonia from farms + NOx → ammonium nitrate), rather than emitted directly.
- **Temperature inversion:** warm air sitting above cold air near the ground acts like a lid, trapping pollution. Common in Po Valley winters.
- **MAE:** mean absolute error, the average size of a forecast error, in µg/m³.
- **RMSE:** like MAE but punishes large errors more.
- **Theil–Sen:** a trend line using the median of all pairwise slopes; robust to outliers.
- **Kendall tau:** a test of whether a series consistently goes up or down.
- **STL:** splits a time series into trend + seasonal + remainder.
- **Placebo test:** apply the same "effect" calculation to years when nothing happened, to see how big an effect looks by chance.
- **Data leakage:** accidentally letting a model see information from the future (or from the test set) during training.
- **Block bootstrap:** resampling chunks of consecutive days many times to estimate uncertainty, keeping neighbouring days together because they are correlated.

---

## 5 likely interview questions

**1. "Walk me through your project in two minutes."**
I wanted to see whether Milan's air is really improving, and whether the 2020 lockdown made a measurable difference. I used ARPA Lombardia's official sensor data from 2015 to today, cleaned it carefully (validity flags, error codes, completeness rules), and found that NO2 fell 45% and PM about 35% in ten years, but levels are still 2–4 times the WHO guidelines. For the lockdown I compared spring 2020 with the same weeks in other years using three methods and a placebo test: NO2 dropped about 30–40% beyond normal variation, but PM didn't, because most PM in the Po Valley is secondary. Finally, I built a next-day PM10 forecast evaluated on a strict time-based split; it beats the naive baseline by about 9%, and the main way to improve it would be weather data.

**2. "What was the hardest decision, and why did you make it the way you did?"**
How to compare the lockdown fairly. The easy answer, "−43% NO2 vs previous years", overstates the effect because pollution was already falling. So I added a trend-adjusted comparison and a ratio to each year's own winter, plus a placebo test. The number got smaller (around −30 to −40%) but more believable, and it also showed that the PM "drop" wasn't real.

**3. "Your gradient boosting model didn't beat linear regression. Isn't that a failure?"**
No, it's a result. Model selection on held-out years picked the linear model, and on the test set the two were within 0.15 µg/m³. With lag and calendar features, the relationship is mostly linear: today's level, reversion to the average, and the season. The real bottleneck is missing information (weather), not model complexity. I'd rather report that honestly than tune LightGBM on the test set until it wins.

**4. "How do you know your forecast evaluation is honest?"**
Three things. First, features only use data up to day *t*, and a unit test checks that changing the future doesn't change past features. Second, the split is chronological: I chose the model using only 2015–2023 and evaluated on 2024–2025 once. Third, I compared against the persistence baseline and used a block bootstrap to show the improvement (0.33–1.09 µg/m³) is above zero.

**5. "What are the limitations, and what would you do with more time?"**
Coverage: only 2–5 urban stations, and only 2 for PM2.5. No weather data, which is the main confounder for the lockdown and the main missing input for forecasting. The lockdown result is strong evidence, not causal proof. Next I'd add ARPA's meteorological data to build a "de-weathered" model: train on 2015–2019 to predict pollution from weather, then compare predicted vs actual for spring 2020. The same weather features would improve the forecast too.

---

## Things that went wrong (good stories for an interview)

- **The "NA" pitfall:** pandas silently turned ARPA's validity flag "NA" into a missing value. I caught it because a cross-tab of flag vs error code didn't add up.
- **A claim I had to correct:** I first wrote that 2025 was the first year all stations met the EU PM10 limit. The table showed one station had 36 days (limit 35), so I corrected it.
- **A hypothesis that was only partly right:** I expected the lockdown to erase the morning traffic peak. It shrank, but the biggest drop was in the afternoon.
- **Leap-day artifact:** a strange dip in the multi-year average turned out to be 29 February existing only in 2016; I removed that date when aligning calendars.
