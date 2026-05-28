#!/usr/bin/python3
#
#   apt-find-non-downloadable - Find installed packages that are not downloadable via configured APT sources.
#
#   Copyright (C) 2014-2026   Jan Hilberath <jan@hilberath.de>
#
#   This program is free software; you can redistribute it and/or modify it
#   under the terms of the GNU General Public License as published by the
#   Free Software Foundation; either version 2 of the License, or (at your
#   option) any later version.
#
#   This program is distributed in the hope that it will be useful, but
#   WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY
#   or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License
#   for more details.
#
#   You should have received a copy of the GNU General Public License along
#   with this program; if not, write to the Free Software Foundation, Inc.,
#   51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#

__version__ = '0.4.0'

import argparse
import sys

from apt import Package
from apt.cache import LockFailedException, FetchFailedException, Filter, FilteredCache, Cache
from loguru import logger


class InstalledFilter(Filter):
    def apply(self, pkg: Package) -> bool:
        return pkg.is_installed


def main():
    arg_parser = argparse.ArgumentParser(
        description='Find installed packages that are not downloadable via configured APT sources.',
        prog='apt-find-non-downloadable'
    )
    arg_parser.add_argument("-s", "--silent", help="be silent, only print found package's names", action="store_true")
    arg_parser.add_argument("-v", "--version", action='version', version='%(prog)s ' + __version__)
    args = arg_parser.parse_args()

    logger.remove()
    logger.add(
        sys.stdout,
        colorize=True,
        format="<level>{level: <8}</level> | <level>{message}</level>"
    )

    cache = Cache(progress=None, rootdir=None, memonly=True)
    try:
        if not args.silent:
            logger.info('Updating APT cache (in memory)...')
        cache.update(fetch_progress=None)
    except (FetchFailedException, LockFailedException) as e:
        if not args.silent:
            logger.error(e)
            logger.warning(f'Using outdated cache.')
    cache.open()

    filtered_cache = FilteredCache(cache)
    filtered_cache.set_filter(InstalledFilter())

    print()

    # num_of_cached_packages = len(cache)
    # if 0 == num_of_cached_packages:
    #     logger.error('No cached packages found.')
    #     sys.exit(1)

    if not filtered_cache:
        logger.error('No installed packages found.')
        sys.exit(1)

    if not args.silent:
        logger.info(f'Checking {len(filtered_cache)} installed (of {len(cache)} cached) packages...')

    non_downloadable_pkgs = set()
    for pkg_name in filtered_cache.keys():
        pkg: Package = filtered_cache[pkg_name]
        if not (pkg.installed.downloadable or pkg.candidate.downloadable):
            non_downloadable_pkgs.add(pkg)

    print_packages(sorted(non_downloadable_pkgs), args.silent)


def print_packages(pkgs, silent):
    if silent:
        for pkg in pkgs:
            print(pkg.name)
    else:
        if pkgs:
            print('')
            logger.error(f'Found {len(pkgs)} non-downloadable packages.')
            print('')
            name_max_len = len(max(pkgs, key=lambda pkg: len(pkg.name)).name)
            installed_version_max_len = len(max(pkgs, key=lambda pkg: len(pkg.installed.version)).installed.version)

            for pkg in pkgs:
                print(
                    '{:s}   {:s}   {:s}'.format(
                        pkg.name.ljust(name_max_len),
                        pkg.installed.version.ljust(installed_version_max_len),
                        pkg.installed.summary
                    )
                )
        else:
            print('')
            logger.info('No non-downloadable packages found.')


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Exiting...")
        sys.exit(10)
