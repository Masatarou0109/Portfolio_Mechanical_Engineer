# CAE解析結果に基づく設計判断レポート自動生成ツール

## Automated CAE Design Review Tool

このリポジトリは、Nastranの解析結果を設計判断に使える指標へ変換し、比較・判定・報告を自動化するPythonツールです。

This repository provides a Python tool that imports Nastran analysis results and automates comparison, judgement, and reporting for engineering design review.

---

## 何が嬉しいのか

CAD/CAEツールはコンター図の表示に強いですが、複数ケースの比較、許容値超過面積率、改善率、安全率、OK/Warning/NG判定、報告用Excelの作成は手作業になりやすいです。

This tool focuses on the post-processing work that often remains manual after contour visualization: multi-case comparison, exceeded-area ratio, improvement rate, safety factor, OK/Warning/NG judgement, and Excel report generation.

---

## 主な機能

- 複数のCAE結果CSVを一括読み込み
- NastranのBDFから節点・シェル要素の形状情報を読み込み
- NastranのF06/PCH系テキスト結果から変位、温度、応力、熱流束を読み込み
- 最大温度、最大ミーゼス応力、最大変位をケースごとに比較
- 面積加重平均を計算
- 許容温度・許容応力・許容変位に対するOK/Warning/NG判定
- 許容値を超えた領域の面積率を算出
- ベースラインからの改善率を算出
- 熱流束 × 面積による総熱量を算出
- 細かい熱流束分布を粗いブロック平均に置き換えた場合の誤差を評価
- Excelレポート、Markdownレポート、比較グラフを自動出力

---

## Nastran入力

Nastran結果を使う場合は、`data/nastran_cases.csv` を用意します。

```csv
case_id,case_description,bdf_path,result_path
case_01_baseline,Nastran baseline demo,nastran_demo/demo_model.bdf,nastran_demo/case_01_baseline.f06
case_02_nastran_update,Nastran improved demo,nastran_demo/demo_model.bdf,nastran_demo/case_02_nastran_update.f06
```

サンプルとして `data/nastran_cases.example.csv` と `data/nastran_demo/` を同梱しています。

対応しているNastran入力は以下です。

| Input | 読み取り内容 |
|---|---|
| BDF | `GRID`, `CTRIA3`, `CQUAD4` から要素中心座標、要素面積、構成節点を取得 |
| F06/PCH text | displacement vector, grid point temperature, element von Mises stress, element heat flux |

F06/PCHの書式はNastranのバージョンや出力設定で差が出るため、このポートフォリオでは代表的なテキストテーブルを対象にしています。実務でOP2バイナリを直接読む場合は、`pyNastran` を使う拡張が自然です。

既存のCSVデモも残しているため、`data/nastran_cases.csv` が存在しない場合は従来どおり `data/case_*.csv` を読み込みます。

## CSVデモ入力の想定列

| Column | Meaning |
|---|---|
| case_id | 解析ケース名 |
| case_description | ケース説明 |
| element_id | 要素ID |
| x_mm, y_mm | 要素中心座標 |
| area_mm2 | 要素面積 |
| stress_vm_mpa | ミーゼス応力 |
| displacement_mm | 変位 |
| temperature_c | 温度 |
| heat_flux_w_mm2 | 熱流束 |
| block_id | 粗い平均化領域ID |

CSVサンプルデータおよびNastranデモデータは疑似CAEデータであり、実業務データや機密情報は含みません。

The sample data is synthetic and does not contain confidential CAE results.

---

## 実行方法

```bash
pip install -r requirements.txt
python src/run_review.py
```

Nastranデモを使う場合:

```bash
cp data/nastran_cases.example.csv data/nastran_cases.csv
python src/run_review.py
```

---

## 出力ファイル

| Output | Description |
|---|---|
| outputs/design_review_report.xlsx | 設計レビュー用Excelレポート |
| outputs/design_review_report.md | Markdown形式の設計レビュー要約 |
| outputs/case_summary.csv | ケース別サマリー |
| outputs/risk_elements.csv | 許容値を超えた要素一覧 |
| outputs/block_average_error_summary.csv | ブロック平均化による熱流束誤差サマリー |
| outputs/case_comparison_temperature.png | 最大温度のケース比較図 |
| outputs/case_comparison_stress.png | 最大応力のケース比較図 |
| outputs/case_comparison_displacement.png | 最大変位のケース比較図 |
| outputs/case_comparison_exceeded_area.png | 許容温度超過面積率の比較図 |

---

## 設計判定ロジック

判定基準は `config/design_criteria.json` で管理します。

Judgement criteria are managed in `config/design_criteria.json`.

例：

```json
{
  "temperature_limit_c": 118.0,
  "temperature_warning_c": 110.0,
  "stress_allowable_mpa": 200.0,
  "stress_yield_mpa": 320.0,
  "displacement_limit_mm": 0.235,
  "minimum_safety_factor": 1.5
}
```

実案件で使う場合は、材料、設計規格、社内基準、試験条件に合わせて必ず変更してください。

For real projects, these values must be replaced with project-specific limits based on material properties, design standards, internal criteria, and test conditions.

---

## ポートフォリオとして見せたいポイント

この作品の主役はコンター図の再描画ではありません。主役は、CAE結果を設計判断に変換するワークフローです。

The main purpose of this project is not to redraw contour plots. The core value is converting CAE results into design-review decisions.

具体的には、以下を示します。

- Nastranの解析結果をPythonで読み込み、設計評価指標へ変換できる
- 最大値だけでなく、超過面積率で危険度を評価できる
- 設計変更前後の改善率を定量化できる
- 同じ判定基準で複数ケースを一括評価できる
- Excelレポートまで自動生成できる

---

## 注意

このツールはポートフォリオ用のデモです。実際の設計判断に使う場合は、メッシュ品質、境界条件、材料物性、単位系、荷重条件、接触条件、解析収束性を別途確認してください。

This tool is a portfolio demonstration. For real engineering decisions, mesh quality, boundary conditions, material properties, unit systems, loading conditions, contact settings, and solver convergence must be verified separately.
