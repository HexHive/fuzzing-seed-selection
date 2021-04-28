#!/usr/bin/env python3

"""
Run multiple fuzzing campaigns in parallel.

Author: Adrian Herrera
"""


from argparse import ArgumentParser, Namespace
from concurrent.futures import ProcessPoolExecutor as Executor
from csv import DictWriter
from datetime import datetime
from pathlib import Path
from shutil import which
from subprocess import PIPE, run
from time import sleep
from typing import TextIO
import gzip
import logging
import os
import re

from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler

from seed_selection.log import FORMATTER as LOG_FORMATTER
from seed_selection.argparse import mem_limit, path_exists, positive_int


AFL_SEED_RE = re.compile(r'''^id[:_]''')
TIMESTAMP_FIELDNAMES = ('seed', 'size', 'unix_time', 'time_offset')


class FuzzEventHandler(PatternMatchingEventHandler):
    """Only capture testcase creation events."""

    def __init__(self, logger: logging.Logger) -> None:
        patterns = [
            str(Path('*') / 'crashes' / 'id:*'),
            str(Path('*') / 'hangs' / 'id:*'),
            str(Path('*') / 'queue' / 'id:*'),
        ]
        super().__init__(patterns=patterns)
        self._logger = logger

    def on_created(self, event) -> None:
        super().on_created(event)
        self._logger.info(event.src_path)


def parse_args() -> Namespace:
    """Parse command-line arguments."""
    parser = ArgumentParser(description='Run a fuzzer experiment')
    parser.add_argument('-j', '--jobs', type=positive_int,
                        default=os.cpu_count() // 3,
                        help='Number of concurrent fuzz campaigns')
    parser.add_argument('-i', '--input', metavar='DIR', type=path_exists,
                        required=True,
                        help='Path to the input corpus directory')
    parser.add_argument('-o', '--output', metavar='DIR', type=Path,
                        required=True,
                        help='Path to the output results directory')
    parser.add_argument('-t', '--timeout', default=None, type=positive_int,
                        help='Timeout for each run')
    parser.add_argument('-m', '--memory', type=mem_limit, default=None,
                        help='Memory limit for child process')
    parser.add_argument('-n', '--nodes', type=positive_int, default=2,
                        help='Number of fuzzer nodes')
    parser.add_argument('-w', '--watch', action='store_true',
                        help='Watch the output directory and generate timestamps')
    parser.add_argument('--num-trials', type=positive_int, default=30,
                        help='The number of repeated trials to perform')
    parser.add_argument('--trial-len', type=positive_int, default=18 * 60 * 60,
                        help='The length of an individual trial (in seconds)')
    parser.add_argument('--cmp-log', metavar='BIN', type=Path,
                        help='Path to cmp-log instrumented binary (if fuzzing '
                             'with AFL++)')
    parser.add_argument('target', metavar='TARGET', type=path_exists,
                        help='Target program')
    parser.add_argument('target_args', metavar='ARG', nargs='*',
                        help='Target program arguments')
    return parser.parse_args()


def get_logger(log_file: TextIO) -> logging.Logger:
    """Create a logger for recording file creation events."""
    handler = logging.StreamHandler(log_file)
    handler.setFormatter(LOG_FORMATTER)

    name = '.'.join(log_file.name.split(os.sep)[-3:])
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)

    return logger


def create_watchdog(logger: logging.Logger, fuzz_dir: Path) -> Observer:
    """Create a watchdog observer for recording file creation events."""
    handler = FuzzEventHandler(logger)
    observer = Observer()
    observer.schedule(handler, fuzz_dir, recursive=True)

    return observer


def timestamp_results(out_dir: Path, start_time: datetime) -> dict:
    """Timestamp the results of AFL."""
    stats = []

    for root, dirs, files in os.walk(out_dir):
        # Ignore hidden directories
        dirs[:] = [d for d in dirs if not d[0] == '.']

        for name in files:
            if not AFL_SEED_RE.match(name):
                continue

            seed = Path(root) / name
            ctime = seed.stat().st_ctime

            stat_dict = dict(seed=str(seed), unix_time=ctime,
                             time_offset=ctime - start_time.timestamp(),
                             size=seed.stat().st_size)
            stats.append(stat_dict)

    return stats


def run_fuzzer(afl: Path, out_dir: Path, node: int, **kwargs) -> int:
    """Run a fuzzer, and log testcases as they are created."""
    # Create AFL command-line. We use `timeout` because a timeout in
    # subprocess.run causes us to lose our `CompletedProcess` object
    args = ['timeout', '%ds' % kwargs['trial_len'],
            afl, '-i', str(kwargs['input']), '-o', str(out_dir.parent)]

    if kwargs['timeout']:
        args.extend(['-t', str(kwargs['timeout'])])
    if kwargs['memory'] and not kwargs['cmp_log']:
        args.extend(['-m', kwargs['memory']])

    if node == 1:
        args.extend(['-M', out_dir.name])
    else:
        args.extend(['-S', out_dir.name])

    if kwargs['cmp_log']:
        args.extend(['-m', 'none', '-c', str(kwargs['cmp_log'])])
    if 'fuzzer_args' in kwargs:
        args.extend(kwargs['fuzzer_args'])

    args.extend(['--', str(kwargs['target']), *kwargs['target_args']])

    # Create AFL environment
    env = os.environ.copy()
    env['AFL_NO_UI'] = '1'

    # Create watchdog. Testcase creation times are logged to a compressed file
    if kwargs['watch']:
        log_file = gzip.open(out_dir / 'watchdog.log.gz', 'wt')
        logger = get_logger(log_file)
        watchdog = create_watchdog(logger, out_dir)
        watchdog.start()

    # Start the fuzzer
    try:
        start_time = datetime.now()
        print('[%s] %s' % (start_time, ' '.join(args)))
        proc = run(args, stdout=PIPE, stderr=PIPE, env=env, check=False)

        # Save fuzzer output
        with open(out_dir / 'stdout.log', 'wb') as outf:
            outf.write(proc.stdout)
        with open(out_dir / 'stderr.log', 'wb') as outf:
            outf.write(proc.stderr)

        # Timestamp everything produced by the fuzzer
        stats = []
        for name in ('queue', 'crashes', 'hangs'):
            stats.extend(timestamp_results(out_dir / name, start_time))
        stats.sort(key=lambda d: d['unix_time'])
        with open(out_dir / 'timestamps.csv', 'w') as outf:
            writer = DictWriter(outf, fieldnames=TIMESTAMP_FIELDNAMES)
            writer.writeheader()
            writer.writerows(stats)

        return proc.returncode
    finally:
        # Cleanup
        watchdog.stop()
        watchdog.join()
        log_file.close()

    return None


def main():
    """The main function."""
    args = parse_args()

    afl = which('afl-fuzz')
    if not afl:
        raise Exception('Cannot find `afl-fuzz`. Check PATH')

    num_jobs = args.jobs
    num_nodes = args.nodes

    if num_jobs % num_nodes != 0:
        raise Exception('The number of jobs (%d) must be divisible by the '
                        'number of nodes (%d)' % (num_jobs, num_nodes))

    out_dir = args.output
    out_dir.mkdir(exist_ok=True)

    with Executor(max_workers=num_jobs) as executor:
        for trial in range(1, args.num_trials + 1):
            # Create output directory
            trial_dir = args.output / f'trial-{trial:02d}'
            trial_dir.mkdir(exist_ok=True)

            # Run the fuzzer node
            for node in range(1, 1 + args.nodes):
                node_dir = trial_dir / f'fuzzer-{node:02d}'
                node_dir.mkdir(exist_ok=True)

                # Sleep to avoid races when AFL attempts to bind to a core
                executor.submit(run_fuzzer, afl, node_dir, node, **vars(args))
                sleep(1.5)


if __name__ == '__main__':
    main()
