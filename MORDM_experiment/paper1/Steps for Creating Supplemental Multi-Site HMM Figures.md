

1. Run `make_mhmm_figures.py` for Steps 1-4. This code fits the multi-site hidden Markov model, creates Figure S12-14 which assess goodness of fit of the model, and creates an example 110-year synthetic streamflow sample (`AnnualQ_s.csv`). 
2. Run `daily_disaggregation.py` to disaggregate `AnnualQ_csv` to a daily timescale (`DailyQ_s.csv`).
3. Run `make_mhmm_figures.py` for Step 5. This code creates Figures S10-11 which are correlation heat map plots that assess how well the model is maintaining spatial correlation in the synthetic traces. 
4. Run `aggregate_synthetic_traces.R` to aggregate the ensemble of synthetic traces (in `./calfews_src/data/MGHMM_synthetic/`) across locations.
5. Run `make_mhmm_figures.py` for Step 6 to create Figure S7 which creates synthetic and historical flow duration curves at specific locations.  