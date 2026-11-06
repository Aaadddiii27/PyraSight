"""Fix data leakage in mesogeos training script."""
import os

path = r'C:\Aditya Folder\Projects\PyraSight\ml\mesogeos_hazard\train.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Replace the EXCLUDE_COLS definition
old_line = 'EXCLUDE_COLS = {"time", "time_idx", "sample", "ignition_points", "burned_areas"}'
new_lines = (
    '# EXCLUDE columns that directly encode fire outcomes (data leakage)\n'
    '# burned_area_has: 0 in all negatives, >0 in all positives -- perfect separator\n'
    '# burned_areas: active fire flag -- direct outcome\n'
    '# ignition_points: fire ignitions -- direct outcome\n'
    'EXCLUDE_COLS = {\n'
    '    "time", "time_idx", "sample",\n'
    '    "ignition_points",\n'
    '    "burned_areas",\n'
    '    "burned_area_has",\n'
    '}'
)

if old_line in content:
    content = content.replace(old_line, new_lines)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Fixed: burned_area_has now excluded from features")
else:
    print("Pattern not found. Checking content around EXCLUDE_COLS...")
    idx = content.find('EXCLUDE_COLS')
    print(repr(content[max(0, idx-20):idx+200]))
