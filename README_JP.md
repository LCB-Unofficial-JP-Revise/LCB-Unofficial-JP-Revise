# Limbus Company - JP Translation Revision

当プロジェクトは、『Limbus Company』公式日本語版に含まれる誤記・一部の誤訳を校正し、それらを修正するためのレポートを提供することを目的としています。


- 校正作業は [ParaTranz](https://paratranz.cn/projects/14860) 上で行っており、その成果をもとにレポートが生成されます。

- 副産物として、ゲームの **カスタム言語機能** を利用したModも公開しています。これはプロジェクトの参加者が、修正内容をゲーム上で確認できるようにするためのものです。

## 📄 成果物

- `report_general.csv`  
  校正レポート

- `report_storydata.csv`  
  校正レポート (ストーリー関連)

- `Localize_Fixed/jp_fixed/`  
  校正を取り込んだ日本語翻訳ファイル (JP_,*Json, ファイル構造はLocalize/jp/と同一)

- `Localize_Fixed/jp_mod/`  
  上記の日本語翻訳ファイルから作られたカスタム言語Mod

#### 🔍 簡単な比較方法

[WinMerge](https://winmerge.org/) などの差分比較ソフトで `Localize/jp/` と `Localize_Fixed/jp_fixed/` を比較することで、ファイル間の変更点を簡単にチェックしたり取り込んだりすることができます。

## 🛠 その他の構成物

- `Localize/kr/, Localize/en/, Localize/jp/`  
  公式言語ファイルのバックアップ

- `paratranz/`  
  ParaTranzから取得した翻訳ファイルのバックアップ

- `Utilities/Importer`  
  レポートの自動生成ツール (Localize/*, paratranz/*のファイルを利用)

- `Utilities/`  
  プロジェクトの管理、校正のためのPythomプログラム群

---

## 📝 レポートの区分

生成されるレポート (`report_general.csv` / `report_storydata.csv`) では、以下のカテゴリに分類して修正内容を記載しています。

### ✅ 誤記
日本語訳において明らかに誤っている表記上のミス。以下のようなケースが対象です。

- 脱字
- 衍字（余分な文字）
- 誤変換・タイポ
- 段落の欠落
- 同音異義語の漢字の誤用
- 数値・キーワードの誤記
- 表記揺れ
- その他の明確な誤記

### ❓ 誤訳の疑い
原文の意味と異なる、または原文の意図が適切に反映されていないと考えられる日本語訳。


### 💬 表現改善
日本語として不自然・冗長・または粗い表現を、より自然かつ明確になるよう調整します。以下のようなケースが対象です。

- 全体的な調整を要する、助詞（てにをは）・係り受けの誤り
- 熟語の誤用
- 冗長な繰り返し表現の簡略化
- 日本語として意味を読み取ることが不必要に難しい翻訳
- 難読漢字・熟語のうち、読めないことが妨げとなる箇所へのルビ付加
##### 「誤記」には必ず修正文が含まれていますが、その他のカテゴリでは修正文を含まず、問題点の指摘のみに留まっている場合があります。
---

### 📚 ライセンス
本リポジトリに含まれる翻訳校正レポートおよび関連プログラムは、[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)ライセンスの下で公開されています。  

本リポジトリは、Limbus Companyの公式翻訳言語ファイル群をもとに構成されており、それらに含まれる原文および翻訳文などの著作権その他の知的財産権は、[Project Moon](https://projectmoon.studio)様に帰属します。

このプロジェクトは非公式であり、Project Moon様が保証または関与するものではありません。本リポジトリに含まれる修正提案および派生データは、公式翻訳の品質向上を目的としたものであり、Project Moon様による参考利用を意図しています。

[![License: CC BY 4.0](https://img.shields.io/badge/License-CC%20BY%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by/4.0/)


#### ➕ 追加許諾（CCPlus）

Project Moon様は、本リポジトリに含まれる成果物を、クレジット表示なしで使用・改変・再配布することができます。  
この追加許諾は、[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)ライセンスに基づく通常の権利に加え、[Project Moon](https://projectmoon.studio)様に対して個別に許諾されるものです。
