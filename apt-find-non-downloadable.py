#!/usr/bin/python
#
#   apt-find-non-downloadable - Find installed packages that are not downloadable via configured APT sources.
#
#   Copyright (C) 2014   Jan Hilberath <jan@hilberath.de>
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

import apt
import argparse
import sys


class InstalledFilter(apt.cache.Filter):
    def apply(self, pkg):
        return pkg.is_installed


def main():
    arg_parser = argparse.ArgumentParser(
        description='Find installed packages that are not downloadable via configured APT sources.'
    )
    arg_parser = argparse.ArgumentParser(version='%(prog)s 0.1.0')
    arg_parser.add_argument("-s", "--silent", help="be silent, only print found package's names", action="store_true")
    args = arg_parser.parse_args()

    cache = apt.Cache(progress=None, rootdir=None, memonly=True)
    cache.update()
    cache.open(None)
    num_of_cached_packages = len(cache)
    if 0 == num_of_cached_packages:
        print('No cached packages found.')
        sys.exit(1)

    filtered_cache = apt.cache.FilteredCache(cache)
    filtered_cache.set_filter(InstalledFilter())
    num_of_filtered_packages = len(filtered_cache)
    if 0 == num_of_filtered_packages:
        print('No installed packages found.')
        sys.exit(1)

    if not args.silent:
        print(
            'Checking {:d} installed (of {:d} cached) packages...'.format(
                num_of_filtered_packages,
                num_of_cached_packages
            )
        )

    non_downloadable_pkgs = set()
    for pkg_name in filtered_cache.keys():
        pkg = filtered_cache[pkg_name]
        if not (pkg.installed.downloadable or pkg.candidate.downloadable):
            non_downloadable_pkgs.add(pkg)

    print_packages(sorted(non_downloadable_pkgs), args.silent)


def print_packages(pkgs, silent):
    if silent:
        for pkg in pkgs:
            print(pkg.name)
    else:
        if 0 == len(pkgs):
            print('')
            print('No non-downloadable packages found.')
        else:
            print('')
            print('Found {:d} non-downloadable packages:'.format(len(pkgs)))
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


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(10)
