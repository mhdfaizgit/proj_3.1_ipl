# Statistical Validation Report

## Purpose

This report records the statistical validation performed in Step 4. Each tested finding is documented with the claim, statistical test, result, effect size where applicable, sample size, and a plain-English verdict.

## T1. Does winning the toss help you win the match?

### Claim
Winning the toss helps a team win the match.

### Hypothesis
- **H₀:** The toss winner's true match-win rate is 50%.
- **H₁:** The toss winner's true match-win rate is different from 50%.

### Test
Binomial test.

### Result
- Decisive matches: **1,187**
- Toss winner also won: **613**
- Observed win rate: **51.64%**
- p-value: **0.2700**
- 95% Wilson confidence interval: **48.80%–54.48%**
- Effect: **1.64 percentage points above 50%**

### Verdict
**NOT SIGNIFICANT.**

The p-value is greater than 0.05, so we fail to reject H₀. There is insufficient evidence that winning the toss changes the chance of winning the match.

---

## T2. Does the decision taken after the toss matter?

### Claim
The decision made after winning the toss is associated with match outcome.

### Hypothesis
- **H₀:** Batting first and fielding first have the same win rate.
- **H₁:** Their win rates are different.

### Test
Chi-square test of independence.

### Result
- Bat first: **184 wins, 218 losses**
- Bat-first win rate: **45.77%**
- Field first: **429 wins, 356 losses**
- Field-first win rate: **54.65%**
- Difference: **8.88 percentage points**
- Chi-square: **8.04**
- p-value: **0.0046**
- Degrees of freedom: **1**

### Verdict
**SIGNIFICANT.**

The p-value is less than 0.05, so we reject H₀. The decision taken after the toss is associated with match outcome. The guide notes that this is another view of the chase advantage tested in T3, rather than a completely separate effect.

---

## T3. Does the chasing team have an advantage?

### Claim
The chasing team has an advantage.

### Hypothesis
- **H₀:** The chase win rate is 50%.
- **H₁:** The chase win rate is different from 50%.

### Test
Binomial test.

### Result
- Decisive matches: **1,187**
- Successful chases: **647**
- Chase win rate: **54.51%**
- Difference from 50%: **4.51 percentage points**
- p-value: **0.0021**
- 95% Wilson confidence interval: **51.66%–57.32%**

### Verdict
**SIGNIFICANT.**

The p-value is less than 0.05, so we reject H₀. There is evidence that the chase win rate differs from 50%, with the observed rate being above 50%.
---

## T4. Does chase win rate fall as the target rises?

### Claim
The chance of winning a chase decreases as the target becomes larger.

### Hypothesis
- **H₀:** Chase win rates are the same across target bands.
- **H₁:** Chase win rates are not the same across target bands.

### Test
Chi-square test of independence.

### Result
- Target bands: **5**
- Highest chase win rate: **82.6%** for targets under 140
- Lowest chase win rate: **23.2%** for targets of 200+
- Difference: **approximately 59 percentage points**
- Chi-square: **197.68**
- Degrees of freedom: **4**
- p-value: **approximately 1 × 10⁻⁴¹**

### Verdict
**SIGNIFICANT.**

The p-value is far below 0.05, so we reject H₀. Chase outcome is strongly associated with target band, with much lower chase success at higher targets.

---

## T5. Are defended totals actually bigger than chased ones?

### Claim
Teams that defend a total score more in the first innings, on average, than teams whose target is successfully chased.

### Hypothesis
- **H₀:** The mean first-innings scores of the two groups are equal.
- **H₁:** The mean first-innings scores are different.

### Test
Independent two-sample t-test with unequal variances.

### Result
- Defended matches: **540**
- Successful chase matches: **647**
- Defended average: **183.3 runs**
- Chased average: **155.5 runs**
- Difference: **27.8 runs**
- t-statistic: **15.73**
- p-value: **1.17 × 10⁻⁵⁰**
- Cohen's *d*: **0.92**
- Effect-size interpretation: **Large**

### Verdict
**SIGNIFICANT, AND LARGE.**

The p-value is far below 0.05, so we reject H₀. The average first-innings score is substantially higher in defended matches, and the effect size is large.

---

## T6. Is powerplay really faster than middle overs?

### Claim
Teams score faster during the powerplay than during the middle overs.

### Hypothesis
- **H₀:** Powerplay and middle-over scoring rates are the same.
- **H₁:** The two scoring rates are different.

### Test
Paired t-test.

### Result
- Valid innings: **2,406**
- Powerplay average: **8.02 runs/over**
- Middle-over average: **7.95 runs/over**
- Difference: **approximately 0.08 runs/over**
- t-statistic: **1.53**
- p-value: **0.1259**

### Verdict
**NOT SIGNIFICANT.**

The p-value is greater than 0.05, so we fail to reject H₀. There is insufficient evidence of a measurable difference between powerplay and middle-over scoring rates in this test. Therefore, the Step 3 finding that powerplay is faster does not hold statistically.

---

## T7. Do left-handers really hit harder than right-handers?

### Claim
Left-handed batters have a higher strike rate than right-handed batters.

### Hypothesis
- **H₀:** Left-handed and right-handed batters have the same average strike rate.
- **H₁:** Their average strike rates are different.

### Test
Independent two-sample t-test with unequal variances.

### Result
- Total batters: **137**
- Left-handed batters: **50**
- Right-handed batters: **87**
- Left-handed average strike rate: **136.60**
- Right-handed average strike rate: **136.62**
- Difference: **-0.02**
- p-value: **0.9942**
- Cohen's *d*: **0.001**
- Effect-size interpretation: **Essentially zero**

### Verdict
**NOT SIGNIFICANT, WITH ESSENTIALLY ZERO EFFECT.**

The p-value is greater than 0.05, so we fail to reject H₀. There is insufficient evidence that left-handed and right-handed batters have different average strike rates. The effect size is essentially zero.

---

## T8. Are spinners genuinely cheaper than fast bowlers?

### Claim
Spin bowlers concede fewer runs per over than pace bowlers.

### Hypothesis
- **H₀:** Spin and pace bowlers have the same average economy rate.
- **H₁:** Their average economy rates are different.

### Test
Independent two-sample t-test with unequal variances.

### Result
- Total bowlers: **149**
- Spin bowlers: **51**
- Pace bowlers: **98**
- Spin average economy: **7.70**
- Pace average economy: **8.49**
- Difference: **0.79 runs/over**
- p-value: **approximately 1 × 10⁻¹⁰**
- Cohen's *d*: **1.19**
- Effect-size interpretation: **Large**

### Verdict
**SIGNIFICANT, AND LARGE.**

The p-value is far below 0.05, so we reject H₀. Spin and pace bowlers have significantly different average economy rates, with a large observed effect.

---

## T9. Does Sawai Mansingh really favour the chasing team?

### Claim
Chasing works better at Sawai Mansingh Stadium than elsewhere.

### Hypothesis
- **H₀:** The stadium's chase win rate is the same as the league rate of 54.51%.
- **H₁:** The stadium's chase win rate is different from 54.51%.

### Test
Binomial test.

### Result
- Matches at the stadium: **66**
- Chase wins: **43**
- Stadium chase win rate: **65.15%**
- League chase win rate: **54.51%**
- Difference: **10.64 percentage points**
- p-value: **0.0849**
- 95% Wilson confidence interval: **53.11%–75.52%**

### Verdict
**NOT SIGNIFICANT — CANNOT TELL.**

The p-value is greater than 0.05, so we fail to reject H₀. The data are insufficient to determine whether Sawai Mansingh Stadium genuinely favours chasing.

---

## T10. Has scoring genuinely risen across the seasons?

### Claim
Average IPL innings scores have risen across the seasons.

### Hypothesis
- **H₀:** Season and average innings score have no meaningful relationship.
- **H₁:** Season and average innings score are related.

### Test
Pearson correlation.

### Result
- Seasons: **19**
- First-season average score: **154.6**
- Latest-season average score: **184.0**
- Pearson correlation (*r*): **0.862**
- *R²*: **0.743**
- p-value: **0.0000021**

### Verdict
**SIGNIFICANT, WITH A STRONG POSITIVE RELATIONSHIP.**

The p-value is less than 0.05, so we reject H₀. There is a strong positive relationship between season and average innings score. The *R²* value of 0.743 means that about 74.3% of the variation in average score is associated with the linear relationship with season.

Correlation does not establish causation. Possible alternative explanations include changes in batting technology, rules, boundary sizes, venues, and teams or squads.

---

## T11. Is Mumbai's head-to-head record over Chennai real?

### Claim
Mumbai Indians have the better head-to-head record against Chennai Super Kings.

### Hypothesis
- **H₀:** Mumbai Indians win 50% of their matches against Chennai Super Kings.
- **H₁:** Mumbai Indians' win rate is different from 50%.

### Test
Binomial test.

### Result
- Head-to-head matches: **40**
- Mumbai Indians wins: **21**
- Mumbai win rate: **52.5%**
- p-value: **0.8746**

### Verdict
**NOT SIGNIFICANT.**

The p-value is greater than 0.05, so we fail to reject H₀. The observed 21–19 record is compatible with an evenly matched result. There is insufficient evidence that Mumbai Indians have a genuine head-to-head advantage.

---

## T12. Does the chasing advantage change from season to season?

### Claim
Some seasons favour chasing more than others.

### Hypothesis
- **H₀:** The chase win rate is the same across seasons.
- **H₁:** The chase win rate is not the same across seasons.

### Test
Chi-square test of independence.

### Result
- Seasons: **19**
- Lowest chase win rate: **42.9%**
- Highest chase win rate: **68.3%**
- Spread: **25.4 percentage points**
- Chi-square: **20.34**
- Degrees of freedom: **18**
- p-value: **0.3141**

### Verdict
**NOT SIGNIFICANT.**

The p-value is greater than 0.05, so we fail to reject H₀. Although chase win rates varied between seasons, there is insufficient evidence that the differences represent a genuine season-to-season change rather than random variation.

---

## T13. Do the bowling styles really differ in how much they concede?

### Claim
The eight main bowling styles do not all concede runs at the same rate.

### Hypothesis
- **H₀:** All eight bowling styles have the same true economy rate.
- **H₁:** At least one bowling style has a different economy rate.

### Test
One-way ANOVA.

### Result
- Bowling styles tested: **8**
- Lowest average economy: **7.47 runs/over**
- Highest average economy: **8.63 runs/over**
- Difference: **1.16 runs/over**
- F-statistic: **6.99**
- p-value: **approximately 0.000001**

### Verdict
**SIGNIFICANT.**

The p-value is less than 0.05, so we reject H₀. The eight bowling styles do not all concede at the same rate. ANOVA establishes that at least one group differs, but it does not identify which specific pair differs.

--- 

# Final Verdict

### Findings supported by statistical validation

- **T2:** Toss decision is associated with match outcome.
- **T3:** Chase win rate differs from 50%.
- **T4:** Chase success differs substantially by target band.
- **T5:** Defended totals are substantially higher than totals in successful chases.
- **T8:** Spin and pace bowlers have significantly different economy rates.
- **T10:** Average innings score has a strong positive relationship with season.
- **T13:** The eight main bowling styles do not all have the same economy rate.

### Findings not supported by statistical validation

- **T1:** Winning the toss does not show a statistically significant effect.
- **T6:** The powerplay-versus-middle-over difference is not statistically significant.
- **T7:** No meaningful difference was found between left- and right-handed batter strike rates.
- **T11:** The Mumbai–Chennai head-to-head record does not provide significant evidence of an advantage.
- **T12:** Seasonal variation in chase win rate is not statistically significant.

### Finding where the data are insufficient

- **T9:** The evidence is insufficient to determine whether Sawai Mansingh Stadium genuinely favours chasing.

## Statistical Decision Rule

The validation uses a **0.05 significance level**:

- **p < 0.05:** statistically significant → reject H₀.
- **p ≥ 0.05:** not statistically significant → fail to reject H₀.

A non-significant result does **not** prove that H₀ is true. It means that the available evidence is not strong enough to reject H₀.


