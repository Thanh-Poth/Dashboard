# Quant Trading Dashboard: Data, Alphas, ML and Backtesting in One Interface

> A full-stack web application that takes a quantitative research workflow from **market data collection** to **alpha generation**, **machine-learning model optimization** and **backtesting**, all driven from a React interface on top of a FastAPI backend.

![Python](https://img.shields.io/badge/Backend-FastAPI-009688) ![React](https://img.shields.io/badge/Frontend-React-61DAFB) ![Domain](https://img.shields.io/badge/Domain-Quantitative%20Trading-darkgreen)

<!-- VERIFY: add 1-2 screenshots of the Data, Alpha and Backtest tabs here: ![Backtest tab](docs/backtest.png) -->

---

## TL;DR for recruiters

| | |
|---|---|
| **Problem** | Quant research usually lives in scattered notebooks. It is hard to re-run, compare and present. |
| **Solution** | One application that chains the whole workflow behind an API and a UI: data -> features -> alphas -> selection -> model -> backtest. |
| **Skills shown** | Full-stack development (Python API + React), applied machine learning on financial data, quantitative research workflow, system design. |

---

## Features

| Tab | What it does |
|---|---|
| **Data** | Collects market data from Yahoo Finance and MetaTrader 5. |
| **Alpha** | Generates features and candidate alpha signals, then selects the most useful ones. |
| **Model** | Optimizes a machine-learning model on the selected alphas (the trained model is stored in `saved_model/`). |
| **Backtest** | Runs a backtest of the resulting strategy and displays the results. |
| **Menu** | Navigation across the workflow. |

---

## Architecture

```
React frontend (App, Menu, Data, Alpha, Backtest)
          |  HTTP / JSON
          v
FastAPI backend (main.py)
   |-- data collection (Yahoo / MT5)
   |-- feature & alpha generation and selection
   |-- ML model optimization
   '-- backtesting engine
          |
          v
saved_model/   persisted trained model
```

<!-- VERIFY: confirm which ML framework produces saved_model/1 and which endpoints exist, then name them here. -->

---

## Repository layout

```
project/        Application source (backend + frontend)
saved_model/1   Serialized trained model
```

<!-- VERIFY: expand the tree once the folder structure inside project/ is confirmed. -->

---

## Quick start

```bash
# Backend
uvicorn main:app --reload

# Frontend
npm install
npm start
```

<!-- VERIFY: exact folders and commands (e.g. cd project/backend, cd project/frontend, npm run dev). -->

---

## Related project

The risk and portfolio layer (risk parity, Kelly sizing, VaR budgeting, causal walk-forward backtest) lives in [Strategy_Backtesting_Pipeline](https://github.com/Thanh-Poth/Strategy_Backtesting_Pipeline) and is designed to be exposed through this dashboard (for example behind a `POST /portfolio/backtest` endpoint).

---

## Skills demonstrated

**Full-stack**: FastAPI, REST/JSON, React components and state, API-to-UI integration
**Data / ML**: financial data collection, feature engineering, alpha selection, model optimization, backtesting
**Product thinking**: turning a research pipeline into a usable tool

---

## Author

**Thanh Son Potherat**: engineering student focused on quantitative finance, machine learning and data science.
[GitHub](https://github.com/Thanh-Poth) | [LinkedIn](https://www.linkedin.com/in/thanh-son-potherat-b793b333a/)
