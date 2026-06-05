import sys
import argparse
import subprocess

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--title', required=True)
    args = parser.parse_args()
    title = args.title

    steps = [
        (1, 'Fetch post',          'Scripts/step1_fetch.py',          ['--title', title]),
        (2, 'Extract prose',       'Scripts/step2_extract.py',        []),
        (3, 'Rewrite prose',       'Scripts/step3_rewrite.py',        []),
        (4, 'Reinsert prose',      'Scripts/step4_reinsert.py',       []),
        (5, 'Inject ld+json',      'Scripts/step5_inject_ldjson.py',  ['--title', title]),
        (6, 'Save output',         'Scripts/step6_save_output.py',    ['--title', title]),
        (7, 'DeepSeek review',     'Scripts/step7_review.py',         []),
        (8, 'Quality gate',        'Scripts/step8_quality_gate.py',   []),
    ]

    total = len(steps)
    for step_num, label, script, extra_args in steps:
        print(f'=== Step {step_num}/{total}: {label} ===')
        result = subprocess.run([sys.executable, script] + extra_args)

        if step_num <= 6:
            if result.returncode != 0:
                print(f'Error in step {step_num}: {label}. Pipeline stopped.')
                sys.exit(1)
        elif step_num == 7:
            if result.returncode == 1:
                print('WARNING: DeepSeek found critical issues. Check Temp/output_review.txt. Continuing.')
        elif step_num == 8:
            if result.returncode == 1:
                print('WARNING: Quality gate found issues. Check Temp/quality_gate_report.txt. Output saved.')

    print('Pipeline complete.')

if __name__ == '__main__':
    main()

