from __future__ import print_function
from datetime import datetime as dt
from dateutil import parser as ps
import locale
import os
import glob
from operator import itemgetter

def prettify(number):

    # Adds thousands commas to a number.

    locale.setlocale(locale.LC_ALL, 'en_US.utf8')
    pretty_number = locale.format("%d", number, grouping=True)
    # TODO: Update to return 2 dec places
    return pretty_number


def lazy_dt(string='2016-12-31'):

    # Returns the number of days elapsed since a given 
    # date string.

    date = ps.parse(string)
    now = dt.now()
    elapsed = int(str(now-date).split()[0])
    years = round(elapsed/365, 2)
    answer = '{} days (or {} years)'.format(prettify(elapsed), years)
    # TODO: Update to prettify(years) once prettify is updated
    return answer


def get_file(file_pattern, target_dir=None, description = 'file'):

    # Helps the user find the file matching the description and filename
    # prefix, prompts the user to chooose one if there are more than one, 
    # complains if there is none, and returns the full filename otherwise.

    if target_dir:
        target_dir = os.path.abspath(target_dir)
    else: 

        # Solicit the file location from the user.

        cwd = os.getcwd()
        home = os.path.expanduser('~')
        dls = '{}/Downloads'.format(home)
        locs = {1: {'desc': 'In this folder', 'path': cwd},
                2: {'desc':'In the Downloads folder', 'path': dls},
                3: {'desc': 'Other', 'path': home}}
        print('Where is the {}?'.format(description))
        for loc in locs:
            print(loc, ': ', locs[loc]['desc'], ' (', locs[loc]['path'], ')', sep='')
        while target_dir == None:
            try:
                choice = int(input('> '))
                target_dir = locs[choice]['path']
            except (ValueError, KeyError):
                print("\nCouldn't parse that; please try again.")

    # Find the matching file(s); pick one or complain if not exactly one. 

    files = glob.glob('{}/{}'.format(target_dir, file_pattern))
    if not files:
        print("ERROR: No source file found. Please refer to "\
              "your documentation for "\
              "instructions on how to create a source file for this report.\n")
        raise Exception('There was an error with the source data.')
    elif len(files) == 1:
        filename = files[0]
        print('Found it:', filename)
    elif len(files) > 1:
        print("More than one file found. Please select the one containing "\
            " the most current", description, ":\n")
        for i, file in enumerate(files):
            print(i+1, ': ', file, sep='')
        filename = files[int(input('> ').strip())-1]
    return filename

def print_options(options, purpose='', choose=False, sort=True):

    # Displays a list of options for the user, and optionally 
    # makes them choose one.

    print('Enter your choice{}:'.format(purpose))
    for i, option in enumerate(sorted(options, key=itemgetter(1))):
        print('   {}. {}'.format(i + 1, option.name))
    if choose:
        while True:
            try:
                choice = int(input('   > '))-1
            except (ValueError, TypeError):
                print("I couldn't parse that; please try again?")
                continue
            for i, option in enumerate(sorted(options, key=itemgetter(1))):
                if i == choice:
                    return options[option]
            print(choice+1, 'wasn\'t an option, sorry!')


def save(data, target_loc):
    if os.path.isfile('./{}'.format(target_loc)):
        existing_files_today = 1
        while os.path.isfile('./{}({})'.format(target_loc, existing_files_today)):
            existing_files_today += 1
        target_loc = '{}({})'.format(target_loc, existing_files_today)
    with open(target_loc, 'w') as outfile:
        for record in data:
            record = '{}\n'.format(record) if record[-1:] != '\n' else record
            outfile.write(record)
    print('Saved them in', target_loc)
