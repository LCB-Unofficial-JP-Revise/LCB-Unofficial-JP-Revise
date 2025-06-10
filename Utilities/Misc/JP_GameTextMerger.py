import os
import json
import re
from collections import OrderedDict


CUSTOM_FILE_ORDER_PATH = "JP_GameTextMerger_Rules.txt"

# Directory paths and prefixes
JP_DIR = ("Localize/jp", "JP_")
KR_DIR = ("Localize/kr", "KR_")
EN_DIR = ("Localize/en", "EN_")

model_json = f"{JP_DIR[0]}/{JP_DIR[1]}ScenarioModelCodes-AutoCreated.json"

OUTPUT_DIR = "txt_output"
DEL_DUPLICATES = True # Trueにすると重複行を出力しない（Storyテキストには影響なし）

TARGET_KEYS = {'abName', 'abnormalityName', 'add', 'area', 'askLevelUp', 
'behaveDesc', 'chapter', 'chapterNumber', 'chaptertitle', 'clue', 'codeName', 
'company', 'content', 'desc', 'description', 'dialog', 'dlg', 'eventDesc', 'failureDesc', 
'flavor', 'longName', 'lowMoraleDescription', 'message', 'messageDesc', 'min', 'name', 
'nameWithTitle', 'nickName', 'openCondition', 'panicDescription', 'panicName', 'parttitle', 
'place', 'prevDesc', 'rawDesc', 'shortName', 'simpleDesc', 'story', 'subDesc', 'successDesc', 
'summary', 'teller', 'title', 'variation', 'variation2', 'model'}

"""
ゲーム翻訳テキスト校正支援ツール

【概要】
このプログラムは、ゲームの多言語対応JSONファイルから翻訳テキストを抽出し、
校正作業を効率化するための単一テキストファイルを生成するツールです。
複数のJSONファイルに分散したテキストを言語別に統合し、
校正者が一つのファイルで全体の翻訳を確認・修正できる環境を提供します。
日本語(JP)、韓国語(KR)、英語(EN)の3言語に対応しています。

【主な機能】
1. 複数のJSONファイルから翻訳対象テキストを一括抽出
2. 校正用の言語別統合テキストファイル生成
3. ファイル別の個別テキストファイル出力（詳細確認用）
4. ストーリーファイルの論理的順序でのソート機能
5. 重複テキストの除去による校正効率化（オプション）
6. キャラクター名の自動変換による可読性向上

【ディレクトリ構成】
入力：
- Localize/jp/ (日本語JSONファイル、JP_プレフィックス)
- Localize/kr/ (韓国語JSONファイル、KR_プレフィックス)  
- Localize/en/ (英語JSONファイル、EN_プレフィックス)

出力：
- txt_output/jp/ (日本語個別ファイル)
- txt_output/kr/ (韓国語個別ファイル)  
- txt_output/en/ (英語個別ファイル)
- txt_output/*_all_general.txt (一般テキスト校正用統合ファイル)
- txt_output/*_all_story.txt (ストーリーテキスト校正用統合ファイル)

【校正作業での活用】
- *_all_general.txt: ゲーム内UI、アイテム名、説明文等の校正
- *_all_story.txt: ストーリー、会話文等の校正（章順でソート済み）
- 個別ファイル: 特定のファイルの詳細確認・修正時に参照

【使用方法】
1. 各言語のJSONファイルを対応するディレクトリに配置
2. JP_ScenarioModelCodes-AutoCreated.json をLocalize/jp/に配置（キャラクター名変換用）
3. python このファイル名.py を実行
4. txt_outputディレクトリの統合ファイルで校正作業を実施

【設定オプション】
- DEL_DUPLICATES: True/False（重複削除の有無）
- TARGET_KEYS: 抽出対象のJSONキー一覧

【対象JSONキー】
'abName', 'abnormalityName', 'add', 'area', 'askLevelUp', 'behaveDesc', 
'chapter', 'chapterNumber', 'chaptertitle', 'clue', 'codeName', 'company', 
'content', 'desc', 'description', 'dialog', 'dlg', 'eventDesc', 'failureDesc',
'flavor', 'longName', 'lowMoraleDescription', 'message', 'messageDesc', 'min', 
'name', 'nameWithTitle', 'nickName', 'openCondition', 'panicDescription', 
'panicName', 'parttitle', 'place', 'prevDesc', 'rawDesc', 'shortName', 
'simpleDesc', 'story', 'subDesc', 'successDesc', 'summary', 'teller', 'title', 
'variation', 'variation2', 'model'
"""


def create_id_name_dictionary():
    # JSONファイルを読み込む
    with open(model_json, 'r', encoding='utf-8') as file:
        data = json.load(file)
    
    # "id"をキーとし、"name"を値とする辞書を作成
    # nameが空の場合はスキップする
    id_name_dict = {item["id"]: item["name"] for item in data["dataList"] if item["name"]}
#    id_name_dict = {item["id"]: f"[{item["name"]}]" if item["name"] else "[-]" for item in data["dataList"]}

    return id_name_dict

MODEL_NAMES = create_id_name_dictionary()



def extract_target_values(data, root_id=None, path="", skip_top_dataList=True, in_dataList=False):
    id_groups = {}
    id_key_order = {}
    id_has_array = {}

    # 新しい：IDに連番を付けて一意化し、順番を保持
    root_id_map = {}  # {original_id: count}
    def get_unique_root_id(original_id):
        count = root_id_map.get(original_id, 0) + 1
        root_id_map[original_id] = count
        return f"{original_id}#{count}"

    def _extract_values(data, root_id=None, path="", skip_top_dataList=True, in_dataList=False):
        values = OrderedDict()

        if isinstance(data, dict) and "dataList" in data and isinstance(data["dataList"], list):
            dataList = data["dataList"]
            for item in dataList:
                if isinstance(item, dict) and "id" in item and "title" in item and "desc" in item:
                    if isinstance(item["desc"], str):
                        item["desc"] += "<JSON_CRLF>"

        if isinstance(data, dict):
            current_id = data.get("id")
            if root_id is None and current_id is not None:
                root_id = get_unique_root_id(str(current_id))

            for key, val in data.items():
                if key == "id" and path != "":
                    continue

                if skip_top_dataList and path == "" and key == "dataList":
                    values.update(_extract_values(val, root_id, path="", skip_top_dataList=False, in_dataList=True))
                    continue

                new_path = f"{path}.{key}" if path else key

                if isinstance(val, str) and key in TARGET_KEYS:
                    if key == 'teller':
                        val = f"[{val}]" if val else "[...]"
                    elif key == 'title':
                        val = f"({val})" if val else val
                    elif key == 'place':
                        val = f"- {val} -" if val else val
                    elif key == 'model':
                        model_name = MODEL_NAMES.get(val)
                        val = f"[{model_name}]" if model_name else ""

                    # コメントアウト処理（root_id == '-1' かつ content の場合）
                    if root_id:
                        if root_id.startswith('-1'):
                            val = f"// {val}"

                    final_key = f"{root_id}-{new_path}" if root_id else new_path
                    values[final_key] = val

                    if root_id:
                        id_groups.setdefault(root_id, []).append(final_key)
                        id_key_order.setdefault(root_id, []).append(final_key)
                else:
                    if isinstance(val, list) and root_id:
                        id_has_array[root_id] = True

                    values.update(_extract_values(val, root_id, new_path, skip_top_dataList=False, in_dataList=False))

        elif isinstance(data, list):
            if root_id:
                id_has_array[root_id] = True

            for index, item in enumerate(data):
                if isinstance(item, str):
                    if path:
                        final_key = f"{root_id}-{path}[{index}]" if root_id else f"{path}[{index}]"
                        values[final_key] = item
                        if root_id:
                            id_groups.setdefault(root_id, []).append(final_key)
                            id_key_order.setdefault(root_id, []).append(final_key)
                else:
                    if in_dataList:
                        values.update(_extract_values(item, root_id, path, skip_top_dataList=False, in_dataList=False))
                    else:
                        new_path = f"{path}[{index}]" if path else f"[{index}]"
                        values.update(_extract_values(item, root_id, new_path, skip_top_dataList=False, in_dataList=False))

        return values

    processed_data = json.loads(json.dumps(data))
    _extract_values(processed_data, root_id, path, skip_top_dataList, in_dataList)
    all_values = _extract_values(processed_data, root_id, path, skip_top_dataList, in_dataList)

    for id_val, keys in id_groups.items():
        if keys and id_has_array.get(id_val, False):
            last_key = id_key_order[id_val][-1]
            if last_key in all_values:
                all_values[last_key] += "<JSON_CRLF>"

    return all_values



def find_matching_files():
    results = {}
    for dir_name, prefix in [JP_DIR, KR_DIR, EN_DIR]:
        files_dict = {}
        # 各ディレクトリ内を再帰的に検索
        for root, _, files in os.walk(dir_name):
            for f in files:
                if f.startswith(prefix) and f.endswith(".json"):
                    # 完全なファイルパスを取得
                    full_path = os.path.join(root, f)
                    # ベースディレクトリからの相対パスを取得
                    relative_path = os.path.relpath(full_path, dir_name)
                    # プレフィックスを削除（ファイル名のみ）
                    file_name = os.path.basename(relative_path)
                    if file_name.startswith(prefix):
                        file_name = file_name[len(prefix):]
                    
                    # ディレクトリパスを取得
                    dir_path = os.path.dirname(relative_path)
                    # ディレクトリパスとプレフィックスなしのファイル名を結合
                    normalized_path = os.path.join(dir_path, file_name)
                    
                    # 対応表に追加
                    files_dict[normalized_path] = relative_path
        
        results[dir_name] = files_dict
    
    return results["Localize/jp"], results["Localize/kr"], results["Localize/en"]

def restore_crlf_in_text(text):

    result = re.sub(r'(<JSON_CRLF>)+', '\n----------', text)

#    result = text.replace('<JSON_CRLF>', '\n----------')
#    result = text
    return result

def process_translation_files(base_name, jp_file, kr_file, en_file, jp_all_texts, kr_all_texts, en_all_texts, 
                              jp_story_texts, kr_story_texts, en_story_texts):
    jp_path = os.path.join(JP_DIR[0], jp_file)
    kr_path = os.path.join(KR_DIR[0], kr_file) if kr_file else None
    en_path = os.path.join(EN_DIR[0], en_file) if en_file else None
    
    # Check if this is a story file (using case-insensitive check)
    is_story_file = "storydata" in jp_path.lower() if jp_path else False
    
    # Load JSON files
    try:
        with open(jp_path, "r", encoding="utf-8") as f:
            jp_data = json.load(f)
        if is_story_file:
            for idx, entry in enumerate(jp_data.get('dataList', [])):
                # Add sequential ID if 'id' key is missing
                if 'id' not in entry:
                    entry['id'] = idx + 1
                
                # Add 'teller' field if both 'model' and 'teller' are missing
                if 'model' not in entry and 'teller' not in entry:
                    new_entry = {}
                    inserted = False
                    for key, value in entry.items():
                        if not inserted and key == 'content':
                            new_entry['teller'] = ''
                            inserted = True
                        new_entry[key] = value
                    jp_data['dataList'][idx] = new_entry

        jp_values = extract_target_values(jp_data)

        # jp_valuesを作成後、不要な'>> 'エントリを除外
        keys_to_delete = []
        prev_key = None
        prev_value = None
        for key, value in jp_values.items():
#            if prev_value == '[]' and isinstance(value, str) and value.startswith('['):
            if prev_value == '[]' and isinstance(value, str) and value.startswith('['):
                keys_to_delete.append(prev_key)
            elif isinstance(value, str) and prev_value == value and value.startswith('['):
                keys_to_delete.append(prev_key)
            prev_key = key
            prev_value = value

        for key in keys_to_delete:
            jp_values.pop(key, None)

    except Exception as e:
        print(f"Error processing JP file {jp_path}: {e}")
        jp_values = {}

#    if is_story_file:
#        print('jp_values=',jp_values)

    kr_values = {}
    if kr_path and os.path.exists(kr_path):
        try:
            with open(kr_path, "r", encoding="utf-8") as f:
                kr_values = extract_target_values(json.load(f))
        except Exception as e:
            print(f"Error processing KR file {kr_path}: {e}")
    
    en_values = {}
    if en_path and os.path.exists(en_path):
        try:
            with open(en_path, "r", encoding="utf-8") as f:
                en_values = extract_target_values(json.load(f))
        except Exception as e:
            print(f"Error processing EN file {en_path}: {e}")
    
    # Skip processing if all JSON files are empty
    if not jp_values and not kr_values and not en_values:
        return
    
    # ディレクトリとファイル名を取得
    output_path = base_name + ".txt"
    
    # 出力先のパスを作成
    jp_output_path = os.path.join(OUTPUT_DIR, "jp", output_path)
    kr_output_path = os.path.join(OUTPUT_DIR, "kr", output_path)
    en_output_path = os.path.join(OUTPUT_DIR, "en", output_path)
    
    # ディレクトリが存在することを確認
    os.makedirs(os.path.dirname(jp_output_path), exist_ok=True)
    os.makedirs(os.path.dirname(kr_output_path), exist_ok=True)
    os.makedirs(os.path.dirname(en_output_path), exist_ok=True)
    
    # ファイル名(base_name)からセパレータを作成
    separator = f"---------------{base_name}---------------\n"
    
    # 日本語テキストをファイルに書き込む
    if jp_values:
        # 個別のテキストファイルに書き込む
        with open(jp_output_path, "w", encoding="utf-8") as f:
            for key, value in jp_values.items():
                if value.strip():  # 空でない値のみ書き込む
                    value = restore_crlf_in_text(value)
                    f.write(f"{value}\n")
        
        # マージ用のテキストを収集
        jp_file_texts = []
        for key, value in jp_values.items():
            if value.strip():
                jp_file_texts.append(value.strip())
        
        # 該当するリストに追加 (Story or General)
        if jp_file_texts:
            if is_story_file:
                jp_story_texts.append((base_name, jp_file_texts))
            else:
                jp_all_texts.append((base_name, jp_file_texts))
    
    # 韓国語テキストをファイルに書き込む
    if kr_values:
        # 個別のテキストファイルに書き込む
        with open(kr_output_path, "w", encoding="utf-8") as f:
            for key in jp_values.keys():  # 日本語と同じ順序を使用
                value = kr_values.get(key, "").strip()
                if value:  # 空でない値のみ書き込む
                    value = restore_crlf_in_text(value)
                    f.write(f"{value}\n")
        
        # マージ用のテキストを収集
        kr_file_texts = []
        for key in jp_values.keys():
            value = kr_values.get(key, "").strip()
            if value:
                kr_file_texts.append(value)
        
        # 該当するリストに追加 (Story or General)
        if kr_file_texts:
            if is_story_file:
                kr_story_texts.append((base_name, kr_file_texts))
            else:
                kr_all_texts.append((base_name, kr_file_texts))
    
    # 英語テキストをファイルに書き込む
    if en_values:
        # 個別のテキストファイルに書き込む
        with open(en_output_path, "w", encoding="utf-8") as f:
            for key in jp_values.keys():  # 日本語と同じ順序を使用
                value = en_values.get(key, "").strip()
                if value:  # 空でない値のみ書き込む
                    value = restore_crlf_in_text(value)
                    f.write(f"{value}\n")
        
        # マージ用のテキストを収集
        en_file_texts = []
        for key in jp_values.keys():
            value = en_values.get(key, "").strip()
            if value:
                en_file_texts.append(value)
        
        # 該当するリストに追加 (Story or General)
        if en_file_texts:
            if is_story_file:
                en_story_texts.append((base_name, en_file_texts))
            else:
                en_all_texts.append((base_name, en_file_texts))


def load_priority_patterns():
    """優先度パターンファイルを読み込み、ファイル名と優先度の辞書を返す"""
    priority_patterns = {}
    if os.path.exists(CUSTOM_FILE_ORDER_PATH):
        try:
            with open(CUSTOM_FILE_ORDER_PATH, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):  # 空行とコメント行を除外
                        parts = line.split('\t')
                        if len(parts) >= 2:
                            filename = parts[0].strip()
                            try:
                                priority = int(parts[1].strip())
                                # 拡張子を除いたベース名を保存
                                base_name = os.path.splitext(filename)[0]
                                priority_patterns[base_name] = priority
                            except ValueError:
                                print(f"優先度の変換に失敗しました: {line}")
        except Exception as e:
            print(f"優先度パターンファイルの読み込みに失敗しました: {e}")
    return priority_patterns

def write_merged_file(output_path, text_data, remove_duplicates=False, story_texts=False):
    """マージしたテキストをファイルに書き込む"""
    
    # 優先度パターンを読み込み
    priority_patterns = load_priority_patterns()
    
    def extract_sort_info(filename):
        name, _ = os.path.splitext(os.path.basename(filename))
        
        if match := re.match(r'^S(\d+)', name):
            number = match.group(1)
            length = len(number)
            if length == 3:
                chapter_num = int(number[0])
            elif length == 4:
                chapter_num = int(number[:2])
            elif length >= 5:
                chapter_num = int(number[:3])
            else:
                chapter_num = int(number)
            
            # 外部ファイルで指定された優先度があればそれを使用、なければデフォルト値
            group_priority = priority_patterns.get(name, 0)  # S系のデフォルトは0
                
        elif match := re.match(r'^(\d+)D', name):
            chapter_num = int(match.group(1))
            # 外部ファイルで指定された優先度があればそれを使用、なければデフォルト値
            group_priority = priority_patterns.get(name, 1)  # D系のデフォルトは1
        else:
            chapter_num = float('inf')
            # 外部ファイルで指定された優先度があればそれを使用、なければデフォルト値
            group_priority = priority_patterns.get(name, 2)  # 想定外のデフォルトは2
            
        # A/B識別子（デフォルトは'A'より'B'を先にする）
        if name.endswith('B'):
            ab_name = f"{name[0:-1]}_0"
        elif re.match(r'.*I\d*$', name):
            ab_name = re.sub(r'(.*)I(.*)', r'\1_1\2', name)
        elif name.endswith('A'):
            ab_name = f"{name[0:-1]}_2"
        else:
            ab_name = f"{name}_3"
            
        # チャプター番号、グループ優先度、A/B優先度、ファイル名で比較する
        return (chapter_num, group_priority, ab_name, name)

    def sort_key(item):
        base_name, _ = item
        return extract_sort_info(base_name)

    if story_texts:
        text_data = sorted(text_data, key=sort_key)

    lines = []
    for base_name, texts in text_data:
        if texts:
            separator = f"---------------{base_name}---------------\n"
            lines.append(separator)
            if remove_duplicates and story_texts == False:
                unique_texts = []
                seen = set()
                for text in texts:
                    if text.strip() == "<JSON_CRLF>":
                        unique_texts.append(text)
                    elif text not in seen:
                        unique_texts.append(text)
                        seen.add(text)
                for text in unique_texts:
                    text = restore_crlf_in_text(text)
                    lines.append(f"{text}\n")
            else:
                for text in texts:
                    text = restore_crlf_in_text(text)
                    lines.append(f"{text}\n")

    with open(output_path, "w", encoding="utf-8") as f:
        f.writelines(lines)


def process_directories():
    if not os.path.exists(JP_DIR[0]):
        print(f"{JP_DIR[0]} directory not found!")
        return
    elif not os.path.exists(KR_DIR[0]):
        print(f"{KR_DIR[0]} directory not found!")
        return
    elif not os.path.exists(EN_DIR[0]):
        print(f"{EN_DIR[0]} directory not found!")
        return
    
    # 出力ディレクトリを作成
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(os.path.join(OUTPUT_DIR, "jp"), exist_ok=True)
    os.makedirs(os.path.join(OUTPUT_DIR, "kr"), exist_ok=True)
    os.makedirs(os.path.join(OUTPUT_DIR, "en"), exist_ok=True)

    # マッチするファイルのリストを取得
    jp_files, kr_files, en_files = find_matching_files()
    
    # 各ファイルを処理
    print(f"JPファイル数: {len(jp_files)}")
    print(f"KRファイル数: {len(kr_files)}")
    print(f"ENファイル数: {len(en_files)}")
    
    # マージするテキスト用のリスト (一般ファイル用)
    jp_all_texts = []  # (base_name, [text1, text2, ...]) のリスト
    kr_all_texts = []
    en_all_texts = []
    
    # マージするテキスト用のリスト (ストーリーファイル用)
    jp_story_texts = []
    kr_story_texts = []
    en_story_texts = []
    
    processed_count = 0
    for base_name, jp_file in jp_files.items():
        # 対応するKRファイルとENファイルを取得
        kr_file = kr_files.get(base_name)
        en_file = en_files.get(base_name)
        
        # 各言語のファイルを処理し、マージ用テキストを収集
        process_translation_files(
            base_name, jp_file, kr_file, en_file, 
            jp_all_texts, kr_all_texts, en_all_texts,
            jp_story_texts, kr_story_texts, en_story_texts
        )
        processed_count += 1
        
        # 進捗を表示（100ファイルごと）
        if processed_count % 100 == 0:
            print(f"{processed_count} ファイルを処理しました...")
    
    # マージしたファイルを出力 (一般ファイル)
    print("\n一般ファイルのマージを開始...")
    write_merged_file(os.path.join(OUTPUT_DIR, "jp_all_general.txt"), jp_all_texts, DEL_DUPLICATES)
    write_merged_file(os.path.join(OUTPUT_DIR, "kr_all_general.txt"), kr_all_texts, DEL_DUPLICATES)
    write_merged_file(os.path.join(OUTPUT_DIR, "en_all_general.txt"), en_all_texts, DEL_DUPLICATES)
    
    # マージしたファイルを出力 (ストーリーファイル)
    print("ストーリーファイルのマージを開始...")
    write_merged_file(os.path.join(OUTPUT_DIR, "jp_all_story.txt"), jp_story_texts, DEL_DUPLICATES, story_texts=True)
    write_merged_file(os.path.join(OUTPUT_DIR, "kr_all_story.txt"), kr_story_texts, DEL_DUPLICATES, story_texts=True)
    write_merged_file(os.path.join(OUTPUT_DIR, "en_all_story.txt"), en_story_texts, DEL_DUPLICATES, story_texts=True)
    
    print(f"\n合計 {processed_count} ファイルを処理しました。")
    
    # マージ結果の情報を表示
    dup_status = "重複削除済み" if DEL_DUPLICATES else "重複含む"
    
    # ファイル数の計算
    jp_general_files = len(jp_all_texts)
    jp_story_files = len(jp_story_texts)
    kr_general_files = len(kr_all_texts)
    kr_story_files = len(kr_story_texts)
    en_general_files = len(en_all_texts)
    en_story_files = len(en_story_texts)
    
    # テキスト行数の計算
    jp_general_lines = sum(len(texts) for _, texts in jp_all_texts)
    jp_story_lines = sum(len(texts) for _, texts in jp_story_texts)
    kr_general_lines = sum(len(texts) for _, texts in kr_all_texts)
    kr_story_lines = sum(len(texts) for _, texts in kr_story_texts)
    en_general_lines = sum(len(texts) for _, texts in en_all_texts)
    en_story_lines = sum(len(texts) for _, texts in en_story_texts)
    
    print(f"\nマージされたファイル（{dup_status}）:")
    print(f"  一般ファイル:")
    print(f"    jp_all_general.txt: {jp_general_files}ファイル、{jp_general_lines}行")
    print(f"    kr_all_general.txt: {kr_general_files}ファイル、{kr_general_lines}行")
    print(f"    en_all_general.txt: {en_general_files}ファイル、{en_general_lines}行")
    print(f"  ストーリーファイル:")
    print(f"    jp_all_story.txt: {jp_story_files}ファイル、{jp_story_lines}行")
    print(f"    kr_all_story.txt: {kr_story_files}ファイル、{kr_story_lines}行")
    print(f"    en_all_story.txt: {en_story_files}ファイル、{en_story_lines}行")

if __name__ == "__main__":
    process_directories()
    print("処理が完了しました。テキストファイルは txt_output ディレクトリに出力されました。")


