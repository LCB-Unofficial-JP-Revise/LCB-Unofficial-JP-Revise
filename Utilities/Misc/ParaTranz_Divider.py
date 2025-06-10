import os
import shutil
import json

INPUT_DIR = 'paratranz_input'
OUTPUT_DIR = 'paratranz_extracted'

def has_nonempty_cmt_jp(entry):
    original = entry.get('original', '')
    translation = entry.get('translation', '')
    # 「<CMT_JP>」の後ろに実際に何か書かれているかを確認
    for text in [original, translation]:
        if '<CMT_JP>' in text:
            after = text.split('<CMT_JP>')[-1]
            if after.strip():
                return True
    return False

def process_json_file(input_path):
    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    filtered_entries = [entry for entry in data if has_nonempty_cmt_jp(entry)]
    
    # エントリ内の文字列に対して置換処理を適用
    for entry in filtered_entries:
        if 'original' in entry and isinstance(entry['original'], str):
            entry['original'] = entry['original'].replace('\\n', '\n')
        if 'translation' in entry and isinstance(entry['translation'], str):
            entry['translation'] = entry['translation'].replace('\\n', '\n')
        if 'context' in entry and isinstance(entry['context'], str):
            entry['context'] = entry['context'].replace('\\n', '\n')
    
    return filtered_entries

def main():
    shutil.rmtree(OUTPUT_DIR, ignore_errors=True)
    
    for root, _, files in os.walk(INPUT_DIR):
        for file in files:
            if file.lower().endswith('.json'):
                input_file_path = os.path.join(root, file)
                filtered_data = process_json_file(input_file_path)

                if filtered_data:
                    relative_path = os.path.relpath(root, INPUT_DIR)
                    output_dir = os.path.join(OUTPUT_DIR, relative_path)
                    os.makedirs(output_dir, exist_ok=True)

                    output_file_path = os.path.join(output_dir, file)
                    with open(output_file_path, 'w', encoding='utf-8', newline='\n') as f:
                        json.dump(filtered_data, f, ensure_ascii=False, indent=2)

if __name__ == '__main__':
    main()