#!/usr/bin/env python3

"""
This script helps with the triage of crashes into bugs.

The user specifies one or more AFL output directories (that contain crashes) and
either (a) a regular expression or (b) a Python script that will be used to
pattern match on a particular bug.

For example, the bug in guetzli-2017-3-30 in Google's Fuzzer Test Suite
(https://github.com/google/fuzzer-test-suite/tree/master/guetzli-2017-3-30) can
be located by applying the following regex on the ASan output:

    Assertion `coeff % quant == 0' failed.

If a bug pattern is more complex than can be expressed in a regular expression,
a Python script can be provided instead. This Python script must contain a
function with the following signature:

    def is_bug(testcase_path, stdout, stderr):
        # Return `True` or `False` depending on if the crash at `testcase_path`
        # (with the provided `stdout` and `stderr` contents) is the bug of
        # interest.
        pass

A CSV file summarizing the matching bugs is produced.

Author: Adrian Herrera
"""


from argparse import ArgumentParser
from csv import DictWriter
from glob import glob
from importlib import import_module
import os
import re
import subprocess
import sys

from tabulate import tabulate

from seed_selection.afl import FuzzerStats
from seed_selection.afl import read_plot_data


TESTCASE_ID_RE = re.compile(r'^id:(\d{6}),')


def parse_args():
    """Parse command-line arguments."""
    parser = ArgumentParser(description='Determine time-to-bug')
    parser.add_argument('-o', '--output', help='Path to output CSV file')
    parser.add_argument('-a', '--append', default=False, action='store_true',
                        help='Append to an existing output CSV file')
    parser.add_argument('-f', '--first-only', default=False,
                        action='store_true',
                        help='Only record the first matching bug')
    parser.add_argument('--ignore-errors', default=False, action='store_true',
                        help='Skip invalid AFL output directories')
    parser.add_argument('-t', '--target', required=False,
                        help='Overwrite the target program contained in fuzzer '
                             'stats')

    bug_search_group = parser.add_mutually_exclusive_group(required=True)
    bug_search_group.add_argument('--regex',
                                  help='Regular expression used to find bug of '
                                       'interest')
    bug_search_group.add_argument('--py-file',
                                  help='Path to Python script used to find bug '
                                       'of interest')

    parser.add_argument('out_dir', metavar='OUT_DIR', nargs='+',
                        help='Path to output directory')

    return parser.parse_args()


def check_out_dir(path):
    """Check the fuzzer output directory."""
    return os.path.isfile(os.path.join(path, 'fuzzer_stats'))


def load_is_bug_func(path):
    """
    Dynamically load a Python script that contains an `is_bug` function that
    checks whether the given crash is the bug we are interested in.
    """
    if not os.path.isfile(path):
        raise Exception('%s is not a valid Python file' % path)

    dirpath, filename = os.path.split(path)
    modname, _ = os.path.splitext(filename)
    sys.path.insert(0, dirpath)

    mod = import_module(modname)

    try:
        is_bug_func = getattr(mod, 'is_bug')
    except AttributeError as e:
        raise Exception('%s does not contain an `is_bug(stdout, stderr)` '
                        'function' % path) from e

    if not callable(is_bug_func):
        raise Exception('`is_bug` is not a function')

    return is_bug_func


def get_crash_time(out_dir, testcase):
    """Get the time of the crashing testcase from the associated plot_data."""
    match = TESTCASE_ID_RE.match(os.path.basename(testcase))
    if not match:
        raise Exception('Invalid crashing input `%s`' % testcase)
    crash_id = int(match.group(1))

    with open(os.path.join(out_dir, 'plot_data'), 'r') as inf:
        plot_dat = read_plot_data(inf)

    crash_rows = plot_dat.loc[plot_dat.unique_crashes >= (crash_id + 1)]
    if crash_rows.empty:
        raise Exception('Could not find crashing input `%s` in plot_data' %
                        testcase)

    return crash_rows.iloc[0].unix_time


def triage_crashes(out_dir, determine_bug, target=None, env=None, cwd=None,
                   silent=False):
    """
    Generate a list of crashing testcases that match the bug we are interested
    in.

    Returns a list of dictionaries describing the bugs found.
    """
    bugs = []
    crash_dir = os.path.join(out_dir, 'crashes')
    num_replayed_crashes = 0

    if not silent:
        num_crashes = len(glob(os.path.join(crash_dir, 'id:*')))
        print('triaging %d crashes in %s' % (num_crashes, out_dir))

    if not env:
        env = os.environ.copy()

    # Parse AFL's fuzzer_stats
    with open(os.path.join(out_dir, 'fuzzer_stats'), 'r') as stats_file:
        afl_stats = FuzzerStats(stats_file)

    # Walk the crashes
    for root, _, files in os.walk(crash_dir):
        for name in sorted(files):
            if not name.startswith('id:'):
                continue

            # Generate the target command-line for the current crashing testcase
            testcase = os.path.join(root, name)
            target_cmdline, target_input = afl_stats.gen_command_line(testcase)
            if target:
                target_cmdline[0] = target

            env['ASAN_OPTIONS'] = 'detect_leaks=0:%s' \
                                  % env.get('ASAN_OPTIONS', '')

            # This is a gross hack around Google FTS targets
            if target_cmdline[1:] == ['-1']:
                target_cmdline[1] = str(testcase)

            # Replay the crashing testcase
            if not silent:
                cmdline_str = ' '.join(target_cmdline)
                if target_input:
                    cmdline_str = '%s < %s' % (cmdline_str, testcase)
                print('  %s' % cmdline_str)
            proc = subprocess.run(target_cmdline, check=False, env=env, cwd=cwd,
                                  input=target_input, stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE)

            # Determine if it is the bug we are interested in (based either on a
            # Python function or a regular expression)
            if callable(determine_bug):
                is_bug = determine_bug(testcase, proc.stdout, proc.stderr)
            else:
                is_bug = (determine_bug.search(proc.stdout) or
                          determine_bug.search(proc.stderr))

            if is_bug:
                ctime = get_crash_time(out_dir, testcase)
                start_time = afl_stats.start_time
                bug_dict = dict(dir=out_dir, testcase=name)
                if ctime < start_time or ctime > afl_stats.last_update:
                    print('WARNING: Testcase %s creation time %f is invalid' %
                          (testcase, ctime))
                    bug_dict['ctime'] = -1
                    bug_dict['time_offset'] = -1
                else:
                    bug_dict['ctime'] = ctime
                    bug_dict['time_offset'] = ctime - start_time
                bugs.append(bug_dict)
            num_replayed_crashes += 1

    return sorted(bugs, key=lambda d: d['time_offset']), num_replayed_crashes


def main():
    """The main function."""
    args = parse_args()

    # Check if the output directories are valid
    out_dirs = []
    for out_dir in args.out_dir:
        if check_out_dir(out_dir):
            out_dirs.append(out_dir)
        elif not args.ignore_errors:
            raise Exception('%s is not a valid AFL output directory' % out_dir)

    # Determine the bug check
    if args.regex:
        determine_bug = re.compile(args.regex.encode(),
                                   flags=re.MULTILINE | re.DOTALL)
        determine_bug_str = args.regex
    else:
        determine_bug = load_is_bug_func(args.py_file)
        determine_bug_str = args.py_file

    # Get fuzzer stats and bugs
    bugs = {out_dir: triage_crashes(out_dir, determine_bug, args.target)
            for out_dir in out_dirs}

    # Munge the data into a suitable format
    out_data = []
    replayed_crash_count = 0
    for out_dir, (bug_times, num_replayed_crashes) in bugs.items():
        replayed_crash_count += num_replayed_crashes

        # If no bugs were found in this particular trial, we still need to
        # capture the trial in an empty CSV row
        if not bug_times:
            csv_dict = dict(out_dir=os.path.realpath(out_dir),
                            testcase=None, unix_time=None, time_offset=None)
            out_data.append(csv_dict)

        for bug_time in bug_times:
            testcase = bug_time['testcase']
            ctime = bug_time['ctime']
            time_offset = bug_time['time_offset']

            csv_dict = dict(out_dir=os.path.realpath(out_dir),
                            testcase=testcase, unix_time=ctime,
                            time_offset=time_offset)
            out_data.append(csv_dict)
            if args.first_only:
                break

    num_bugs = len([True for d in out_data if d['testcase']])
    fieldnames = ('out_dir', 'testcase', 'unix_time', 'time_offset')
    print('\n%d / %d crashes match `%s`\n' % (num_bugs, replayed_crash_count,
                                              determine_bug_str))

    if args.output:
        # Write the results to the output CSV file
        output_append = args.append
        open_mode = 'a' if output_append else 'w'
        with open(args.output, open_mode) as outf:
            writer = DictWriter(outf, fieldnames=fieldnames)
            if not output_append:
                writer.writeheader()
            writer.writerows(out_data)
    else:
        # Print to screen
        def table_str(d):
            r = []
            r.append('%s' % d['out_dir'])
            r.append('%s' % d['testcase'])
            if d['unix_time'] is not None:
                r.append('%d' % d['unix_time'])
            else:
                r.append(None)
            if d['time_offset'] is not None:
                r.append('%d' % d['time_offset'])
            else:
                r.append(None)
            return r
        print(tabulate((table_str(d) for d in out_data), headers=fieldnames))


if __name__ == '__main__':
    main()
