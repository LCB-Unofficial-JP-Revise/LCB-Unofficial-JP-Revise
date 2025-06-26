import os
import shutil
import json
import re
from collections import OrderedDict
import logging

# 設定
OUTPUT_UPDATED = False  # True: 変更があったファイルのみ出力, False: すべてのファイルを出力

# 現在のバージョンのディレクトリ
JP_DIR = ("Localize\\jp", "JP_")
KR_DIR = ("Localize\\kr", "KR_")
EN_DIR = ("Localize\\en", "EN_")

# 過去のバージョンのディレクトリ
JP_DIR_OLD = ("Localize_old\\jp", "JP_")
KR_DIR_OLD = ("Localize_old\\kr", "KR_")
EN_DIR_OLD = ("Localize_old\\en", "EN_")

OUTPUT_DIR = "json_output"

TARGET_KEYS = {'abName', 'abnormalityName', 'add', 'area', 'askLevelUp', 
'behaveDesc', 'chapter', 'chapterNumber', 'chaptertitle', 'clue', 'codeName', 
'company', 'content', 'desc', 'description', 'dialog', 'dlg', 'eventDesc', 'failureDesc', 
'flavor', 'longName', 'lowMoraleDescription', 'message', 'messageDesc', 'min', 'name', 
'nameWithTitle', 'nickName', 'openCondition', 'panicDescription', 'panicName', 'parttitle', 
'place', 'prevDesc', 'rawDesc', 'shortName', 'simpleDesc', 'story', 'subDesc', 'successDesc', 
'summary', 'teller', 'title', 'variation', 'variation2', 'text'}

# ロギングの設定
logging.basicConfig(
    filename='translation_processing.log',
    filemode='w',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

def extract_target_values(data, root_id=None, path="", skip_top_dataList=True, in_dataList=False):
    values = OrderedDict()
    key_counts = {}  # キーの出現回数を追跡するための辞書

    if isinstance(data, dict):
        current_root_id = root_id
        if current_root_id is None and "id" in data:
            current_root_id = str(data["id"])

        # root_id が "-1" の場合はこのエントリをスキップ
        if current_root_id == "-1":
            return values

        for key, val in data.items():
            if key == "id" and path != "":
                continue  # ネストされた "id" は無視
            # "dataList" のキーは最上位でのみスキップ対象
            if skip_top_dataList and path == "" and key == "dataList":
                values.update(extract_target_values(val, current_root_id, path="", skip_top_dataList=False, in_dataList=True))
                continue
            new_path = f"{path}.{key}" if path else key
            if isinstance(val, str) and key in TARGET_KEYS:
                final_key = f"{current_root_id}-{new_path}" if current_root_id else new_path

                # キーの重複を確認し、必要に応じて接尾辞を追加
                if final_key in values:
                    if final_key not in key_counts:
                        key_counts[final_key] = 1
                    else:
                        key_counts[final_key] += 1

                    # 値が同じであれば上書き、異なる場合は接尾辞を付加
                    if values[final_key] != val:
                        dup_key = f"{final_key}-dup{key_counts[final_key]}"
                        values[dup_key] = val
                    # 値が同じ場合は何もしない（上書きせず既存のエントリを保持）
                else:
                    values[final_key] = val
            else:
                extracted_values = extract_target_values(val, current_root_id, new_path, skip_top_dataList=False, in_dataList=False)

                # 抽出された値の各キー重複をチェック
                for extracted_key, extracted_val in extracted_values.items():
                    if extracted_key in values:
                        if extracted_key not in key_counts:
                            key_counts[extracted_key] = 1
                        else:
                            key_counts[extracted_key] += 1

                        # 値が異なる場合のみ接尾辞を付加
                        if values[extracted_key] != extracted_val:
                            dup_key = f"{extracted_key}-dup{key_counts[extracted_key]}"
                            values[dup_key] = extracted_val
                    else:
                        values[extracted_key] = extracted_val

    elif isinstance(data, list):
        for index, item in enumerate(data):
            if isinstance(item, str):  # 文字列が直接リスト内にある場合の処理
                if path:  # パスが存在する場合のみ処理
                    final_key = f"{root_id}-{path}[{index}]" if root_id else f"{path}[{index}]"
                    values[final_key] = item
            else:
                # dataList直下の項目ではインデックスを含めない
                if in_dataList:
                    extracted_values = extract_target_values(item, root_id, path, skip_top_dataList=False, in_dataList=False)
                else:
                    new_path = f"{path}[{index}]" if path else f"[{index}]"
                    extracted_values = extract_target_values(item, root_id, new_path, skip_top_dataList=False, in_dataList=False)

                # 抽出された値の各キー重複をチェック
                for extracted_key, extracted_val in extracted_values.items():
                    if extracted_key in values:
                        if extracted_key not in key_counts:
                            key_counts[extracted_key] = 1
                        else:
                            key_counts[extracted_key] += 1

                        # 値が異なる場合のみ接尾辞を付加
                        if values[extracted_key] != extracted_val:
                            dup_key = f"{extracted_key}-dup{key_counts[extracted_key]}"
                            values[dup_key] = extracted_val
                    else:
                        values[extracted_key] = extracted_val

    return values

def find_matching_files(is_old_version=False):
    """
    指定されたディレクトリからファイルを検索する
    is_old_version: 過去のバージョンのファイルを検索する場合はTrue
    """
    results = {}
    # 古いバージョンのディレクトリか現在のディレクトリかを選択
    # dir_config = [(JP_DIR_OLD, "JP_"), (KR_DIR_OLD, "KR_"), (EN_DIR_OLD, "EN_")] if is_old_version else [JP_DIR, KR_DIR, EN_DIR]
    dir_config = [JP_DIR_OLD, KR_DIR_OLD, EN_DIR_OLD] if is_old_version else [JP_DIR, KR_DIR, EN_DIR]
    
    for dir_path, prefix in dir_config:
        files_dict = {}
        print('dir_path=', dir_path)
        if os.path.exists(dir_path):  # ディレクトリが存在する場合のみ処理
            for root, _, files in os.walk(dir_path):
                for f in files:
                    if f.startswith(prefix) and f.endswith(".json"):
                        full_path = os.path.join(root, f)
                        relative_path = os.path.relpath(full_path, dir_path)  # 相対パス（サブフォルダ含む）
                        # ここでprefixを除去した base_name をキーとする
                        stripped_key = re.sub(rf'^{re.escape(prefix)}', '', relative_path.replace('\\', '/').split('/')[-1])  # ファイル名部分のprefix除去
                        base_name = os.path.join(os.path.dirname(relative_path), stripped_key).replace('\\', '/')
                        files_dict[base_name] = relative_path.replace('\\', '/')
        results[prefix] = files_dict

    return results["JP_"], results["KR_"], results["EN_"]

def load_json_values(file_path):
    """
    JSONファイルを読み込み、値を抽出する
    """
    if file_path and os.path.exists(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return extract_target_values(json.load(f))
        except Exception as e:
            logging.error(f"エラー: {file_path} の読み込みに失敗 - {e}")
    return {}

def process_translation_files(base_name, jp_file, kr_file, en_file):
    """
    翻訳ファイルを処理し、必要に応じて出力する
    """
    jp_path = os.path.join(JP_DIR[0], jp_file)
    kr_path = os.path.join(KR_DIR[0], kr_file) if kr_file else None
    en_path = os.path.join(EN_DIR[0], en_file) if en_file else None
    
    # 現在のバージョンのJSONファイルを読み込み
    jp_values = load_json_values(jp_path)
    kr_values = load_json_values(kr_path)
    en_values = load_json_values(en_path)

    # すべてのJSONファイルが空（有効なデータがない）場合は処理をスキップ
    if not jp_values and not kr_values and not en_values:
        return
    
    # OUTPUT_UPDATEDがTrue（更新されたファイルのみ出力）かつ過去のバージョンのディレクトリが存在する場合
    if OUTPUT_UPDATED:
        # 過去のバージョンのJSONファイルを読み込み
        old_jp_path = os.path.join(JP_DIR_OLD[0], jp_file) if os.path.exists(JP_DIR_OLD[0]) else None
        old_kr_path = os.path.join(KR_DIR_OLD[0], kr_file) if kr_file and os.path.exists(KR_DIR_OLD[0]) else None
        old_en_path = os.path.join(EN_DIR_OLD[0], en_file) if en_file and os.path.exists(EN_DIR_OLD[0]) else None
        
        old_jp_values = load_json_values(old_jp_path)
        old_kr_values = load_json_values(old_kr_path)
        old_en_values = load_json_values(old_en_path)
        
        # 過去のバージョンと現在のバージョンを比較し、変更があるかどうかを確認
        has_changes = False
        
        # 現在のキーと過去のキーのセットを作成
        current_keys = set(jp_values.keys()) | set(kr_values.keys()) | set(en_values.keys())
        old_keys = set(old_jp_values.keys()) | set(old_kr_values.keys()) | set(old_en_values.keys())
        
        # 削除されたキーを検出
        deleted_keys = old_keys - current_keys
        if deleted_keys:
            logging.info(f"キーを削除: {base_name} - {', '.join(deleted_keys)}")
            has_changes = True
        
        # 追加されたキーまたは変更されたキーを検出
        for key in current_keys:
            jp_text = jp_values.get(key, "").strip()
            kr_text = kr_values.get(key, "").strip()
            en_text = en_values.get(key, "").strip()
            
            old_jp_text = old_jp_values.get(key, "").strip()
            old_kr_text = old_kr_values.get(key, "").strip()
            old_en_text = old_en_values.get(key, "").strip()
            
            if jp_text != old_jp_text or kr_text != old_kr_text or en_text != old_en_text:
                has_changes = True
                break
        
        # 変更がなければ出力をスキップ
        if not has_changes:
            return
    
    # 出力データを作成
    output_data = []
    for key in jp_values.keys():  # `jp_values` の順番通りに処理
        jp_text = jp_values.get(key, "").strip()
        kr_text = kr_values.get(key, "").strip()
        en_text = en_values.get(key, "").strip()

        # すべての値が空ならスキップ
        if not jp_text and not kr_text and not en_text:
            continue

        original = f"{jp_text}\n<CMT_KR>\n<CMT_JP>"
        translation = f"{jp_text}\n<CMT_KR>\n<CMT_JP>"
        stage = 1
        context = "\n".join(filter(None, [
            f"KR:\n{kr_text}" if kr_text else "",
            f"EN:\n{en_text}" if en_text else ""
        ]))
        output_data.append({
            "key": key,
            "original": original,
            "translation": translation,
            "stage": stage,
            "context": context
        })
    
    # 出力データが存在する場合のみファイルを作成
    if output_data:
        # base_nameにはパス区切り文字が含まれる可能性がある
        # ディレクトリ部分とファイル名部分を分離
        dir_part, file_part = os.path.split(base_name)
        file_part = os.path.splitext(file_part)[0]  # 拡張子を削除
        
        # ファイル名からJP_接頭辞を削除
        if file_part.startswith(JP_DIR[1]):
            file_part = file_part[len(JP_DIR[1]):]
        
        # ディレクトリ部分とファイル名部分を再結合
        output_filename = os.path.join(dir_part, file_part)
            
        output_path = os.path.join(OUTPUT_DIR, output_filename + ".json")
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)

def process_directories():
    """
    ディレクトリ処理のメイン関数
    """
    # ログファイルの初期化
    logging.info(f"=== 処理開始 ===")
    
    # 現在のバージョンのディレクトリチェック
    if not os.path.exists(JP_DIR[0]):
        logging.error(f"{JP_DIR[0]} directory not found!")
        print(f"{JP_DIR[0]} directory not found!")
        return
    elif not os.path.exists(KR_DIR[0]):
        logging.error(f"{KR_DIR[0]} directory not found!")
        print(f"{KR_DIR[0]} directory not found!")
        return
    elif not os.path.exists(EN_DIR[0]):
        logging.error(f"{EN_DIR[0]} directory not found!")
        print(f"{EN_DIR[0]} directory not found!")
        return
    
    # 出力ディレクトリをクリア
    shutil.rmtree(OUTPUT_DIR, ignore_errors=True)

    # 現在のバージョンのファイルを取得
    jp_files, kr_files, en_files = find_matching_files(is_old_version=False)
    

#    print(jp_files)

    # OUTPUT_UPDATEDがTrueの場合、過去のバージョンのファイルも取得
    if OUTPUT_UPDATED:
        old_jp_files, old_kr_files, old_en_files = find_matching_files(is_old_version=True)
        
        # 削除されたファイルを検出してログに記録
        if os.path.exists(JP_DIR_OLD[0]):
            for base_name in old_jp_files:
                if base_name not in jp_files:
                    logging.info(f"!!! ファイルを削除 !!!: {base_name}")
    
    # 各ファイルを処理
    for base_name, jp_file in jp_files.items():
        kr_file = kr_files.get(base_name)
        en_file = en_files.get(base_name)
        process_translation_files(base_name, jp_file, kr_file, en_file)

    logging.info(f"=== 処理終了　===")

if __name__ == "__main__":
    process_directories()
    print("処理が完了しました。ログファイルを確認してください。")