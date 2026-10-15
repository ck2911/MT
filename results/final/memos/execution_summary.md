# Execution Summary

Main notebook: `1. thesis_master_notebook.ipynb`.
Main outputs: `results/final/`.

## Rebuild Steps

1. Rebuild processed EU/DE data - completed with exit code 0.
2. Build ECB external-instrument shocks - completed with exit code 0.
3. Build monthly model dataset - completed with exit code 0.
4. Run monthly first-stage tournament - completed with exit code 0.
5. Run information-effect screening - completed with exit code 0.
6. Screen monthly proxies - completed with exit code 0.
7. Run monthly reduced-form LP layer - completed with exit code 0.
8. Run residual diagnostics on the baseline local projections - completed with exit code 0.
9. Render thesis figures in the shared visual style - completed with exit code 0.
10. Render enhancement figures - completed with exit code 0.
11. Generate thesis-facing LaTeX tables - completed with exit code 0.
12. Check final empirical outputs - completed with exit code 0.

## Empirical Outputs

- Monthly first-stage top bridge: d_dfr_eop via target_factor_monthly_easing (F=17.07209368475478, status=fragile_candidate).
- Monthly reduced-form LP cells: 660.
- Proxy candidates screened: 18.
- Monthly stability matrix cells: 60.

Hard-IV treatment claims remain gated. The thesis interpretation is monthly reduced-form and tied to the ECB policy-news shock.
