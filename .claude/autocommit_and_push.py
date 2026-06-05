import subprocess
import sys
import os
from datetime import datetime

def ascii_print(msg):
    print(str(msg).encode('ascii', 'replace').decode('ascii'))

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(script_dir, '..'))

    status_result = subprocess.run(
        ['git', 'status', '--porcelain'],
        capture_output=True,
        cwd=project_root
    )

    if status_result.returncode != 0:
        ascii_print('[autocommit] git status failed, skipping autocommit.')
        sys.exit(0)

    output = status_result.stdout.decode('utf-8', errors='replace').strip()

    if not output:
        ascii_print('[autocommit] Working tree clean, nothing to commit.')
        sys.exit(0)

    ascii_print('[autocommit] Changes detected, staging all files...')
    add_result = subprocess.run(
        ['git', 'add', '-A'],
        capture_output=True,
        cwd=project_root
    )
    if add_result.returncode != 0:
        ascii_print('[autocommit] git add failed, skipping autocommit.')
        sys.exit(0)

    timestamp = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
    commit_msg = f'auto: {timestamp} pre-review/pre-test snapshot'

    ascii_print(f'[autocommit] Committing: {commit_msg}')
    commit_result = subprocess.run(
        ['git', 'commit', '-m', commit_msg],
        capture_output=True,
        cwd=project_root
    )
    if commit_result.returncode != 0:
        ascii_print('[autocommit] git commit failed (maybe nothing to commit), continuing.')
        sys.exit(0)

    ascii_print('[autocommit] Pushing to origin...')
    push_result = subprocess.run(
        ['git', 'push'],
        capture_output=True,
        cwd=project_root
    )
    if push_result.returncode != 0:
        push_stderr = push_result.stderr.decode('utf-8', errors='replace').lower()
        if 'fatal: no configured push destination' in push_stderr:
            ascii_print('[autocommit] Warning: no remote configured, push skipped.')
        else:
            ascii_print('[autocommit] Warning: push failed, but continuing.')
    else:
        ascii_print('[autocommit] Push successful.')

    sys.exit(0)

if __name__ == '__main__':
    main()