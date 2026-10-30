import os
import glob

def replace_in_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    new_content = content.replace('rounded-3xl', 'rounded-xl')
    new_content = new_content.replace('rounded-2xl', 'rounded-lg')
    new_content = new_content.replace('text-[10px]', 'text-xs')
    new_content = new_content.replace('text-[11px]', 'text-sm')
    
    if new_content != content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"Updated {filepath}")

if __name__ == "__main__":
    search_path = "C:/StudentHelpdesk/FRONTEND/src/**/*.tsx"
    for filepath in glob.glob(search_path, recursive=True):
        replace_in_file(filepath)
    print("Done")
