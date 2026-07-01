# Copyright (c) 2026 Supratim Sanyal, SANYALnet Labs. All rights reserved.
# Limited Source-Code Viewing License -- view-only. No execution, modification,
# redistribution, production use, or AI/ML training. Full terms: see LICENSE
# (repo root) or https://github.com/tuklusan/Vagabond-Couple-Blog-Enhancer/blob/master/LICENSE
import os

import argparse

import datetime

import glob

import re



TICKET_DIR = 'Tickets'

TICKET_EXTENSION = '.md'


def safe_ticket_id(raw):
    """Return the canonical 'TICKET-NNNN' id, or None if `raw` is not a plain
    numeric id. Blocks path traversal via ticket_id (TICKET-0035)."""
    if raw is None:
        return None
    m = re.fullmatch(r'(?:TICKET-)?(\d{1,6})', str(raw).strip())
    return f'TICKET-{int(m.group(1)):04d}' if m else None


def ticket_path(ticket_id):
    """Resolve a sanitized ticket id to a path INSIDE TICKET_DIR, or None."""
    canonical = safe_ticket_id(ticket_id)
    if not canonical:
        return None
    path = os.path.join(TICKET_DIR, canonical + TICKET_EXTENSION)
    # Defense in depth: the resolved path must stay within TICKET_DIR.
    root = os.path.realpath(TICKET_DIR)
    if os.path.commonpath([root, os.path.realpath(path)]) != root:
        return None
    return path


def oneline(value):
    """Collapse newlines so a field value cannot inject extra header lines
    (TICKET-0036)."""
    return re.sub(r'[\r\n]+', ' ', value or '').strip()



def ensure_ticket_dir():

    if not os.path.exists(TICKET_DIR):

        os.makedirs(TICKET_DIR)



def get_next_ticket_id():

    ensure_ticket_dir()

    pattern = os.path.join(TICKET_DIR, f'TICKET-*{TICKET_EXTENSION}')

    files = glob.glob(pattern)

    if not files:

        return '0001'

    max_id = 0

    for f in files:

        base = os.path.basename(f)

        if base.startswith('TICKET-') and base.endswith(TICKET_EXTENSION):

            try:

                num = int(base[8:-3])

                if num > max_id:

                    max_id = num

            except ValueError:

                continue

    return f'{max_id + 1:04d}'



def parse_ticket_file(filepath):

    with open(filepath, 'r', encoding='utf-8') as f:

        lines = [line.rstrip('\n') for line in f.readlines()]

    if not lines:

        return {}

    header = lines[0]

    if header.startswith('# '):

        id_title = header[2:]

        if ': ' in id_title:

            ticket_id, title = id_title.split(': ', 1)

            ticket_id = ticket_id.split('-')[1] if '-' in ticket_id else ''

        else:

            ticket_id = id_title.split(' ')[0]

            title = id_title[len(ticket_id)+2:].strip() if len(id_title) > len(ticket_id) else ''

            if ticket_id.startswith('TICKET-'):

                ticket_id = ticket_id[8:]

            else:

                ticket_id = ''

    else:

        return {}

    data = {

        'id': ticket_id,

        'title': title,

        'status': '',

        'priority': '',

        'type': '',

        'created': '',

        'description': '',

        'steps': '',

        'notes': ''

    }

    for line in lines[1:]:

        if ': ' in line:

            key, value = line.split(': ', 1)

            key = key.lower()

            if key == 'steps to reproduce':

                key = 'steps'

            if key in data:

                data[key] = value

    return data



def create_ticket_file(args):

    ensure_ticket_dir()

    created = datetime.datetime.now().strftime('%Y-%m-%d')

    # Retry loop: claim the next id by EXCLUSIVE create so two concurrent 'new'
    # commands cannot grab the same id (TICKET-0037).

    for _ in range(50):

        next_id = get_next_ticket_id()

        filepath = os.path.join(TICKET_DIR, f'TICKET-{next_id}{TICKET_EXTENSION}')

        content = [

            f'# TICKET-{next_id}: {oneline(args.title)}',

            f'Status: Open',

            f'Priority: {oneline(args.priority)}',

            f'Type: {oneline(args.type)}',

            f'Created: {created}',

            f'Description: {oneline(args.desc)}',

            'Steps to Reproduce: ',

            'Notes: '

        ]

        try:

            with open(filepath, 'x', encoding='utf-8') as f:

                f.write('\n'.join(content) + '\n')

        except FileExistsError:

            continue

        print(f'TICKET-{next_id}')

        return

    print('Error: could not allocate a ticket id')



def list_tickets(args):

    ensure_ticket_dir()

    pattern = os.path.join(TICKET_DIR, f'TICKET-*{TICKET_EXTENSION}')

    files = glob.glob(pattern)

    tickets = []

    for f in files:

        ticket_data = parse_ticket_file(f)

        if ticket_data and (not args.status or ticket_data.get('status', '').lower() == args.status.lower()):

            tickets.append(ticket_data)

    tickets.sort(key=lambda x: x.get('id', ''))

    print(f"{'ID':<10} {'Status':<10} {'Priority':<10} {'Type':<10} {'Title':<35}")

    print('-' * 80)

    for t in tickets:

        title = t.get('title', '')

        if len(title) > 35:

            title = title[:32] + '...'

        print(f"{t.get('id', ''):<10} {t.get('status', ''):<10} {t.get('priority', ''):<10} {t.get('type', ''):<10} {title:<35}")



def show_ticket(args):

    filepath = ticket_path(args.ticket_id)

    if not filepath or not os.path.exists(filepath):

        print('Ticket not found')

        return

    ticket = parse_ticket_file(filepath)

    if not ticket:

        print('Error reading ticket')

        return

    print(f"ID: {ticket.get('id', '')}")

    print(f"Title: {ticket.get('title', '')}")

    print(f"Status: {ticket.get('status', '')}")

    print(f"Priority: {ticket.get('priority', '')}")

    print(f"Type: {ticket.get('type', '')}")

    print(f"Created: {ticket.get('created', '')}")

    print(f"Description: {ticket.get('description', '')}")

    print(f"Steps to Reproduce: {ticket.get('steps', '')}")

    print(f"Notes: {ticket.get('notes', '')}")



def update_ticket(args):

    filepath = ticket_path(args.ticket_id)

    if not filepath or not os.path.exists(filepath):

        print('Ticket not found')

        return

    ticket_id = safe_ticket_id(args.ticket_id)

    ticket = parse_ticket_file(filepath)

    if not ticket:

        print('Error reading ticket')

        return

    if args.status:

        ticket['status'] = oneline(args.status)

    if args.notes is not None:

        ticket['notes'] = oneline(args.notes)

    content = [

        f"# TICKET-{ticket['id']}: {ticket['title']}",

        f"Status: {ticket['status']}",

        f"Priority: {ticket['priority']}",

        f"Type: {ticket['type']}",

        f"Created: {ticket['created']}",

        f"Description: {ticket['description']}",

        f"Steps to Reproduce: {ticket['steps']}",

        f"Notes: {ticket['notes']}"

    ]

    with open(filepath, 'w', encoding='utf-8') as f:

        f.write('\n'.join(content) + '\n')

    print(f"Ticket {ticket_id} updated.")



def main():

    parser = argparse.ArgumentParser(description='Ticket management system')

    subparsers = parser.add_subparsers(dest='command')



    new_parser = subparsers.add_parser('new')

    new_parser.add_argument('--title', required=True)

    new_parser.add_argument('--priority', default='Medium')

    new_parser.add_argument('--type', default='Bug')

    new_parser.add_argument('--desc', default='')

    new_parser.set_defaults(func=lambda args: create_ticket_file(args))



    list_parser = subparsers.add_parser('list')

    list_parser.add_argument('--status', required=False)

    list_parser.set_defaults(func=lambda args: list_tickets(args))



    show_parser = subparsers.add_parser('show')

    show_parser.add_argument('ticket_id')

    show_parser.set_defaults(func=lambda args: show_ticket(args))



    update_parser = subparsers.add_parser('update')

    update_parser.add_argument('ticket_id')

    update_parser.add_argument('--status', required=False)

    update_parser.add_argument('--notes', required=False)

    update_parser.set_defaults(func=lambda args: update_ticket(args))



    args = parser.parse_args()

    if hasattr(args, 'func'):

        args.func(args)

    else:

        parser.print_help()



if __name__ == '__main__':

    main()