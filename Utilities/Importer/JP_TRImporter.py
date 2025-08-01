import os
import shutil
import json
import regex
from datetime import datetime
from collections import defaultdict
from natsort import natsort_keygen
import csv
import zipfile
import glob
import requests


# ローカルで実行する場合は True にすること
LOCAL_MODE = False

# True にした場合、レポートのタイムスタンプを更新しない
IGNORE_TIMESTAMP_UPDATE = False

# ---------------------------------------------------

if not LOCAL_MODE:
    TOKEN_ID = os.getenv('PARATRANZ_TOKEN')
    PROJECT_ID = os.getenv('PARATRANZ_PROJECT_ID')

# 入力ディレクトリ設定
IN_DIR_INPUT = os.path.join('Localize', 'jp')
IN_DIR_ARCHIVE = os.path.join('paratranz')

# 出力ディレクトリ設定
OUT_DIR_ROOT = 'Localize_Fixed'
OUT_DIR_JP_FIXED = os.path.join('Localize_Fixed', 'jp_fixed')
OUT_DIR_JP_MOD = os.path.join('Localize_Fixed', 'jp_mod')


REPORT_FILES = {'general': 'report_general.csv', 'story': "report_storydata.csv"}

# ---------------------------------------------------


"""
JP - ParaTranz Translation Importer
=====================================

【概要】
このツールは、ParaTranzプラットフォームから翻訳データを取得し、
既存のJSONファイルに翻訳を適用して、翻訳済みファイルとレポートを生成するツールです。

【使い方】
■ ワークフロー実行時（LOCAL_MODE = False）:
  1-1. リポジトリのGitHub Secrets（環境変数）として以下の2つを登録しておくこと
    * PARATRANZ_PROJECT_ID: プロジェクトのID
    * PARATRANZ_TOKEN: ユーザーのAPIトークン, ParaTranzのプロフィール画面の設定から取得可

  1-2. リポジトリ直下にLocalizeフォルダを追加し、ゲームの言語ファイル（en, jp, krフォルダ）を配置しておくこと

  2. 環境をセットアップ後はRun workflowで手動実行するとレポート・翻訳済みファイルが生成され、リポジトリにコミットされます

■ ローカル実行時（LOCAL_MODE = True）:
  1. LOCAL_MODE = True に設定
  2. 以下のディレクトリ構成を準備:
     - Localize/jp/           : 元のJSONファイル
     - paratranz/             : ParaTranzから手動ダウンロードした翻訳アーカイブ（zip）をこの中に配置
  3. python JP_TRImporter.py で実行

【出力】
- Localize_Fixed/jp_fixed/  : 翻訳が適用されたJSONファイル
- Localize_Fixed/jp_mod/    : MOD用JSONファイル（JP_プレフィックス除去）
- report_general.csv        : レポート
- report_storydata.csv      : ストーリー関連用レポート

"""

def extract_latest_archive():
    """IN_DIR_ARCHIVE内の最新のzipファイルを展開"""
    # アーカイブディレクトリの中身をクリア（ディレクトリが存在する場合）
    if os.path.exists(IN_DIR_ARCHIVE):
        # フォルダのみを削除
        for item in os.listdir(IN_DIR_ARCHIVE):
            item_path = os.path.join(IN_DIR_ARCHIVE, item)
            if os.path.isdir(item_path):
                shutil.rmtree(item_path)
    else:
        os.makedirs(IN_DIR_ARCHIVE, exist_ok=True)

    # zipファイルを検索
    zip_pattern = os.path.join(IN_DIR_ARCHIVE, '*.zip')
    zip_files = glob.glob(zip_pattern)
    
    if not zip_files:
        raise FileNotFoundError(f"No zip files found in {IN_DIR_ARCHIVE}")
    
    # 最新のzipファイルを取得
    latest_zip = max(zip_files, key=os.path.getmtime)
    print(f"Extracting latest archive: {latest_zip}")
    
    # zipファイルを展開
    with zipfile.ZipFile(latest_zip, 'r') as zip_ref:
        zip_ref.extractall(IN_DIR_ARCHIVE)
    
    # 展開されたフォルダ内の [アーカイブ名] + 'utf8/jp' フォルダのパスを取得
    extracted_translation_dir = os.path.join(IN_DIR_ARCHIVE, 'utf8', 'jp')
    
    if not os.path.exists(extracted_translation_dir):
        raise FileNotFoundError(f"Expected translation directory not found: {extracted_translation_dir}")
    
    print(f"Translation directory found: {extracted_translation_dir}")
    return extracted_translation_dir


def load_translations_and_comments_by_filename(paratranz_dir):
    """翻訳ファイルから原文、翻訳文、コメントを読み込む"""
    originals_by_file = {}
    translations_by_file = {}
    sources_by_file = {}
    comments_by_file = {}
    
    # 正規表現パターンを事前コンパイル
    translation_pattern = regex.compile(r'\n?<CMT_.*$', regex.MULTILINE | regex.DOTALL)
    context_pattern = regex.compile(r"KR:\n?|EN:\n?")
    comment_pattern = regex.compile(r"<CMT_KR>|<CMT_JP>")
    
    for root, dirs, files in os.walk(paratranz_dir):
        for filename in [f for f in files if f.endswith(".json")]:
            full_path = os.path.join(root, filename)
            
            with open(full_path, encoding='utf-8') as f:
                data = json.load(f)
                originals = {}
                translations = {}
                sources = {}
                comments = {}

                for item in data:
                    key = item["key"]
                    # 原文処理
                    original = item["original"].replace('\\n', '\n')
                    original = regex.sub(translation_pattern, '', original)
                    originals[key] = original
                    
                    # 翻訳文処理
                    translation = item["translation"].replace('\\n', '\n')
                    translation = regex.sub(translation_pattern, '', translation)
                    translations[key] = translation
                    
                    # コンテキスト処理
                    context = item.get("context")
                    if not context == None:
                        context = context.replace('\\n', '\n')
                        parts = regex.split(context_pattern, item["context"])
                        sources[key] = parts[1].removesuffix('\n') if len(parts) > 1 else ""
                    
                    # コメント処理
                    parts = regex.split(comment_pattern, item["translation"].replace('\\n', '\n'))
                    if len(parts) >= 3:
                        comments[key] = {
                            "CMT_KR": parts[1].removesuffix('\n'),
                            "CMT_JP": parts[2].removesuffix('\n')
                        }
                    else:
                        comments[key] = {"CMT_KR": "", "CMT_JP": ""}

                basename = "JP_" + os.path.splitext(filename)[0]
                originals_by_file[basename] = originals
                translations_by_file[basename] = translations
                sources_by_file[basename] = sources
                comments_by_file[basename] = comments

    return originals_by_file, translations_by_file, sources_by_file, comments_by_file

def load_original_entries(input_root):
    """元のJSONファイルからテキストエントリを読み込む"""
    original_formats = {}
    # 先頭・末尾の空白文字検出用正規表現
    leading_pattern = regex.compile(r'^([\n　 ]+)')
    trailing_pattern = regex.compile(r'([\n　 ]+)$')
    
    for root, _, files in os.walk(input_root):
        for filename in [f for f in files if f.endswith(".json")]:
            input_path = os.path.join(root, filename)
            basename = os.path.splitext(filename)[0]
            
            with open(input_path, 'r', encoding='utf-8') as f:
                try:
                    data = json.load(f)
                    if "dataList" in data:
                        file_formats = {}
                        for item in data["dataList"]:
                            entry_id = item.get("id")
                            if entry_id:
                                collect_text_formats(item, file_formats, entry_id, 
                                                   leading_pattern, trailing_pattern)
                        original_formats[basename] = file_formats
                except json.JSONDecodeError:
                    print(f"Error loading JSON from {input_path}")
                    continue
    
    return original_formats

def collect_text_formats(obj, formats_dict, entry_id, leading_pattern, trailing_pattern, path=""):
    """再帰的にオブジェクトを走査してテキストの書式情報を収集"""
    if isinstance(obj, dict):
        for k, v in obj.items():
            new_path = f"{path}.{k}" if path else k
            if k == "id":
                entry_id = v
            collect_text_formats(v, formats_dict, entry_id, leading_pattern, trailing_pattern, new_path)
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            new_path = f"{path}[{i}]"
            collect_text_formats(item, formats_dict, entry_id, leading_pattern, trailing_pattern, new_path)
    elif isinstance(obj, str):
        full_key = f"{entry_id}-{path}"
        leading_match = regex.match(leading_pattern, obj)
        trailing_match = regex.search(trailing_pattern, obj)
        leading = leading_match.group(1) if leading_match else ""
        trailing = trailing_match.group(1) if trailing_match else ""
        
        # 先頭または末尾に空白がある場合に記録
        if leading or trailing:
            formats_dict[full_key] = {
                "leading": leading,
                "trailing": trailing
            }

def organize_duplicate_translations(translations):
    """重複する翻訳キーを整理"""
    pattern = regex.compile(r'^(.*?)(-dup\d+)?$')
    
    organized_translations = defaultdict(list)
    for key, translation in translations.items():
        match = pattern.search(key)
        if match:
            base_key = match.group(1)
            organized_translations[base_key].append((key, translation))
    
    return organized_translations

def apply_translation_to_obj(obj, translations, original_formats, organized_translations, entry_id, path="", dup_counters=None, filename=""):
    """JSONオブジェクトに翻訳を適用"""
    if dup_counters is None:
        dup_counters = defaultdict(int)
    
    # トップレベルのIDを取得
    if entry_id is None and isinstance(obj, dict) and path == "" and "id" in obj:
        entry_id = obj["id"]
    
    if isinstance(obj, dict):
        for k, v in obj.items():
            new_path = f"{path}.{k}" if path else k
            obj[k] = apply_translation_to_obj(v, translations, original_formats, organized_translations, entry_id, new_path, dup_counters, filename)
    elif isinstance(obj, list):
        for i in range(len(obj)):
            new_path = f"{path}[{i}]"
            obj[i] = apply_translation_to_obj(obj[i], translations, original_formats, organized_translations, entry_id, new_path, dup_counters, filename)
    elif isinstance(obj, str):
        full_key = f"{entry_id}-{path}"
        base_key = full_key
        
        # 重複キーの処理
        if base_key in organized_translations:
            available_translations = organized_translations[base_key]
            if available_translations:
                dup_counters[base_key] += 1
                counter = dup_counters[base_key]
                if counter <= len(available_translations):
                    key, translated_text = available_translations[counter - 1]
                else:
                    key, translated_text = available_translations[-1]
                
                # 書式情報を適用
                if full_key in original_formats:
                    format_info = original_formats[full_key]
                    return format_info.get("leading", "") + translated_text + format_info.get("trailing", "")

                return translated_text
        # 通常の翻訳処理
        elif full_key in translations:
            translated_text = translations[full_key]
            if full_key in original_formats:
                format_info = original_formats[full_key]
                return format_info.get("leading", "") + translated_text + format_info.get("trailing", "")
            return translated_text
    
    return obj

def collect_linewise_indents(file_path):
    """元のJSONファイルの各行インデント（スペース数）を収集"""
    indents = []
    with open(file_path, encoding='utf-8') as f:
        for line in f:
            leading_spaces = len(line) - len(line.lstrip(' '))
            indents.append(leading_spaces)
    return indents

def apply_linewise_indent(original_path, temp_path, final_output_path, insert_trailing_lf=False):
    """元ファイルの行ごとのインデントを適用して最終ファイルを出力"""
    original_indents = collect_linewise_indents(original_path)

    with open(temp_path, encoding='utf-8') as temp_f:
        new_lines = temp_f.readlines()

    if insert_trailing_lf:
        new_lines.append('\n')

    with open(final_output_path, 'w', encoding='utf-8') as final_f:
        for i, line in enumerate(new_lines):
            if i < len(original_indents):
                adjusted_line = ' ' * original_indents[i] + line.lstrip(' ')
            else:
                adjusted_line = line
            final_f.write(adjusted_line)

def check_trailing_newline(file_path):
    """ファイル末尾の改行有無をチェック"""
    with open(file_path, 'rb') as f:
        f.seek(-1, os.SEEK_END)
        return f.read(1) == b'\n'


def find_line_number(file_path, search_text):
    """ファイル内でテキストが出現する行番号を検索"""
    try:
        matching_lines = []
        with open(file_path, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f, start=1):
                if search_text in line:
                    matching_lines.append(str(i))
        
        if matching_lines:
            return ','.join(matching_lines)
    except Exception as e:
        print(f"行番号の取得に失敗しました: {file_path}, エラー: {e}")
    return "-"

def collect_csv_report_rows(input_root, rel_path, basename, sources, originals, translations, comments, full_json_path):
    """CSV出力用の行データを収集"""
    rows = []

    is_storydata = "StoryData" in rel_path.replace("\\", "/")
    csv_key = "story" if is_storydata else "general"

    for key in originals:
        source = sources.get(key, "")
        original = source.replace('\n', '\\n')
        translation = originals.get(key, "").replace('\n', '\\n')
        revised = translations.get(key, "").replace('\n', '\\n')
        cmt = comments.get(key, {"CMT_JP": "", "CMT_KR": ""})

        if not (cmt["CMT_JP"] or cmt["CMT_KR"]):
            continue

        relative_path_to_report = os.path.relpath(full_json_path, input_root).replace('\\', '/')
        line_number = find_line_number(full_json_path, translation)

        kr_comment = cmt["CMT_KR"]
        categories = []
#        if regex.search(r"오식\d*:", kr_comment): # 誤植
        if regex.search(r"오기\d*:", kr_comment): # 誤記
            categories.append("오기")
        if regex.search(r"오역 의심\d*:", kr_comment): # 誤訳の疑い
            categories.append("오역 의심")
        if regex.search(r"표현 개선\d*:", kr_comment): # 表現改善
            categories.append("표현 개선")

        priority = {"오기": 0, "오역 의심": 1, "표현 개선": 2}
        categories.sort(key=lambda x: priority[x])
        category = ", ".join(categories)

        row = [
            f"{relative_path_to_report}:{line_number}",
            key,
            category,
            original,
            translation,
            revised,
            cmt["CMT_JP"].replace('\n', ' '),
            cmt["CMT_KR"].replace('\n', ' ')
        ]
        rows.append((csv_key, row))
    
    return rows

def load_existing_timestamps(csv_path):
    """既存レポートから (경로, 키) をキーにして変更日時をマッピングし、内容も記録"""
    timestamps = {}
    contents = {}
    if os.path.exists(csv_path):
        with open(csv_path, encoding='utf-8-sig') as f:
            reader = csv.reader(f, delimiter='\t')
            headers = next(reader, [])
            date_idx = 2 if len(headers) > 2 and "수정 시각" in headers[2] else None
            for row in reader:
                if len(row) >= 9:
                    path, key = row[0], row[1]
                    timestamp = row[date_idx] if date_idx is not None else ""
                    timestamps[(path, key)] = timestamp
                    contents[(path, key)] = row  # 行全体を格納
    return timestamps, contents


def write_csv_report(output_dir, collected_rows):
    """収集したCSV行をファイルごとに自然順で書き出す"""
    grouped_rows = defaultdict(list)
    for csv_key, row in collected_rows:
        grouped_rows[csv_key].append(row)

    # 自然順のキーを生成
    natkey = natsort_keygen()

    def sort_key(row):
        """1列目の 'path:line' を分解して階層・自然順にソート"""
        full_path, _, line_str = row[0].rpartition(":")
        line_num = int(line_str) if line_str.isdigit() else 0
        path_parts = full_path.split(os.sep)  # ディレクトリ階層に分解
        return (len(path_parts), natkey(full_path), line_num)

    for csv_key, rows in grouped_rows.items():
        csv_name = REPORT_FILES.get(csv_key)
        if LOCAL_MODE:
            report_path = os.path.join(output_dir, csv_name)
            os.makedirs(os.path.dirname(report_path), exist_ok=True)
        else:
            report_path = csv_name

        # 古いレポートを一時保存（比較用）
        old_path = report_path + '.old'
        if os.path.exists(report_path):
            shutil.move(report_path, old_path)
        else:
            old_path = None

        existing_timestamps, existing_rows = load_existing_timestamps(old_path) if old_path else ({}, {})

        now = datetime.now().strftime('%Y-%m-%d')
        updated_rows = []

        for row in rows:
            path, key = row[0], row[1]
            row_key = (path, key)
            old_row = existing_rows.get(row_key)

            if not old_row or row[4:8] != old_row[5:9]:
                if IGNORE_TIMESTAMP_UPDATE:
                    try:
                        timestamp = old_row[2]
                    except:
                        timestamp = now
                else:
                    timestamp = now
            else:
                timestamp = old_row[2]

            updated_row = row[:2] + [timestamp] + row[2:]
            updated_rows.append(updated_row)

        header = [
            "경로", "키", "갱신 시각", "카테고리", "원문", "번역문", # パス, キー, 更新日時, カテゴリ, 原文, 翻訳文,
            "수정문", "(일) 코멘트", "(한) 코멘트" # 修正文, (日)コメント, (韓)コメント
        ]

        with open(report_path, 'w', encoding='utf-8-sig', newline='\r\n') as txtfile:
            txtfile.write('\t'.join(header) + '\n')
            for row in sorted(updated_rows, key=sort_key):
                txtfile.write('\t'.join(row) + '\n')

        if old_path and os.path.exists(old_path):
            os.remove(old_path)


def process_all_json(input_root, translation_root, json_output_lang_root, json_output_mod_root, output_root):
    """各JSONファイルの総処理"""
    
    # 出力ディレクトリをクリア
    if os.path.exists(json_output_lang_root):
        shutil.rmtree(json_output_lang_root, ignore_errors=True)

    # Fontフォルダを残してクリア
    if os.path.exists(json_output_mod_root):
        for item in os.listdir(json_output_mod_root):
            item_path = os.path.join(json_output_mod_root, item)
            if item == 'Font':
                continue
            if os.path.isdir(item_path):
                shutil.rmtree(item_path, ignore_errors=True)
            else:
                os.remove(item_path)
    


    print("Loading translations...")
    originals_by_file, translations_by_file, sources_by_file, comments_by_file = load_translations_and_comments_by_filename(translation_root)
    
    print("Loading original formats...")
    original_formats = load_original_entries(input_root)
    
    # 重複翻訳を整理
    organized_translations_by_file = {}
    for basename, translations in translations_by_file.items():
        organized_translations_by_file[basename] = organize_duplicate_translations(translations)
    
    print("Processing files...")

    all_report_rows = []  # 全レポート行を格納

    for root, _, files in os.walk(input_root):
        for filename in [f for f in files if f.endswith(".json")]:
            input_path = os.path.join(root, filename)
            rel_path = os.path.relpath(input_path, input_root)
            output_path = os.path.join(json_output_lang_root, rel_path)
            output_mod_path = os.path.join(json_output_mod_root, os.path.dirname(rel_path), os.path.basename(rel_path).removeprefix('JP_'))

            # 出力ディレクトリを作成
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            os.makedirs(os.path.dirname(output_mod_path), exist_ok=True)

            # ファイル形式を検出
            has_trailing_newline = check_trailing_newline(input_path)
            
            try:
                with open(input_path, encoding='utf-8') as f:
                    original_json = json.load(f)

                # データ取得
                basename = os.path.splitext(filename)[0]
                translations = translations_by_file.get(basename, {})
                sources = sources_by_file.get(basename, {})
                originals = originals_by_file.get(basename, {})
                comments = comments_by_file.get(basename, {})
                file_formats = original_formats.get(basename, {})
                organized_translations = organized_translations_by_file.get(basename, defaultdict(list))

                # dataListの翻訳処理
                if "dataList" in original_json:
                    dup_counters = defaultdict(int)
                    for i, item in enumerate(original_json["dataList"]):
                        entry_id = item.get("id")
                        if entry_id is not None:
                            original_json["dataList"][i] = apply_translation_to_obj(
                                item,
                                translations,
                                file_formats,
                                organized_translations,
                                entry_id,
                                dup_counters=dup_counters,
                                filename=filename
                            )
                
                # 翻訳済みJSONファイルを出力
                tmp_path = output_path + '_temp'
                with open(tmp_path, 'w', encoding='utf-8') as f:
                    json.dump(original_json, f, ensure_ascii=False, indent=2)

                apply_linewise_indent(original_path=input_path, temp_path=tmp_path, final_output_path=output_path, insert_trailing_lf=has_trailing_newline)
                apply_linewise_indent(original_path=input_path, temp_path=tmp_path, final_output_path=output_mod_path, insert_trailing_lf=has_trailing_newline)

                os.remove(tmp_path)

                # レポート行を収集
                rows = collect_csv_report_rows(
                    input_root=input_root,
                    rel_path=rel_path,
                    basename=basename,
                    sources=sources,
                    originals=originals,
                    translations=translations,
                    comments=comments,
                    full_json_path=input_path
                )
                all_report_rows.extend(rows)

            except Exception as e:
                print(f"Error processing {input_path}: {e}")

    # CSVレポートを出力
    write_csv_report(output_root, all_report_rows)

def download_paratranz_artifact(token_id, projects_id, output_file='paratranz_artifact.zip'):
    """
    ParaTranz からアーティファクトをダウンロードする関数。

    Parameters:
        token_id (str): API トークン。
        projects_id (str or int): プロジェクト ID。
        output_path (str): ダウンロードしたファイルの保存先ファイル名。

    Returns:
        str: 保存されたファイルのパス。
    """
    url = f"https://paratranz.cn/api/projects/{projects_id}/artifacts/download"
    headers = {
        "Authorization": f"Bearer {token_id}"
    }

    print('token_id=',token_id,'projects_id=',projects_id)
    print("Current working directory:", os.getcwd())

    # IN_DIR_ARCHIVE が存在しない場合は作成
    if not os.path.exists(IN_DIR_ARCHIVE):
        os.makedirs(IN_DIR_ARCHIVE)
        print(f"ディレクトリを作成しました: {IN_DIR_ARCHIVE}")

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        output_path = os.path.join(IN_DIR_ARCHIVE, output_file)
        with open(output_path, 'wb') as f:
            f.write(response.content)
        print(f"アーティファクトを保存しました: {output_path}")
        return output_path
    else:
        raise Exception(f"ダウンロードに失敗しました: {response.status_code} - {response.text}")


# メイン実行部
if __name__ == "__main__":

    # ワークフローとして実行時、アーカイブをダウンロードする
    if not LOCAL_MODE:
        archive_path = download_paratranz_artifact(TOKEN_ID, PROJECT_ID)

        # アーカイブを展開し、翻訳ディレクトリのパスを取得
        translation_directory = extract_latest_archive()
        os.remove(archive_path)
    else:
        translation_directory = extract_latest_archive()
    
    process_all_json(
        input_root=IN_DIR_INPUT,
        translation_root=translation_directory,
        json_output_lang_root=OUT_DIR_JP_FIXED, 
        json_output_mod_root=OUT_DIR_JP_MOD, 
        output_root=OUT_DIR_ROOT
    )