import json

with open('config.json', 'r') as f:
    cfg = json.load(f)

print('=== CONFIG VERIFICATION ===')
print(f'Sources configured: {len(cfg["sources"])}')
for k, v in cfg['sources'].items():
    has_correct_user = 'RobertCarucci' in v['file_path']
    print(f'  {k}:')
    print(f'    Sheet: {v["sheet_name"]}')
    print(f'    Path correct: {has_correct_user}')

if 'date_range' in cfg:
    print(f'\nRolling window: {cfg["date_range"]["rolling_window_months"]} months')
else:
    print('\nRolling window: NOT CONFIGURED')

print(f'\nOutput directory: {cfg["output_settings"]["output_directory"]}')
