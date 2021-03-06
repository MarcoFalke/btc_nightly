import argparse
from enum import Enum
import os
import pathlib
import sys
import urllib.request
import re
import shutil


class Bin(Enum):
    OSX = 'OSX'
    WIN = 'WIN'
    LIN64 = 'LIN64'
    ARM32 = 'ARM32'
    ARM64 = 'ARM64'
    RV64 = 'RV64'


def __str__(self):
    return self.value


parser = argparse.ArgumentParser()
parser.add_argument('--bin', type=Bin, choices=list(Bin))
parser.add_argument('--srcdir', type=str)
args = parser.parse_args()

LATEST_URL = 'https://bitcoin.jonasschnelli.ch/gitian/build/nightly/latest'
BUILD_URL = 'https://bitcoin.jonasschnelli.ch/gitian/builds/{}/{}'
if args.bin == Bin.OSX:
    ARCHIVE_SNIP = '-osx64.tar.gz'
    ARCHIVE_RE = 'bitcoin-[a-f0-9]+-osx64\.tar\.gz'
    ARCHIVE_EXT = 'tar.gz'
    EXEEXT = ''
if args.bin == Bin.LIN64:
    ARCHIVE_SNIP = '-x86_64-linux-gnu.tar.gz'
    ARCHIVE_RE = 'bitcoin-[a-f0-9]+-x86_64-linux-gnu(-debug)?\.tar\.gz'
    ARCHIVE_EXT = 'tar.gz'
    EXEEXT = ''
if args.bin == Bin.ARM32:
    ARCHIVE_SNIP = '-arm-linux-gnueabihf.tar.gz'
    ARCHIVE_RE = 'bitcoin-[a-f0-9]+-arm-linux-gnueabihf(-debug)?\.tar\.gz'
    ARCHIVE_EXT = 'tar.gz'
    EXEEXT = ''
if args.bin == Bin.ARM64:
    ARCHIVE_SNIP = '-aarch64-linux-gnu.tar.gz'
    ARCHIVE_RE = 'bitcoin-[a-f0-9]+-aarch64-linux-gnu(-debug)?\.tar\.gz'
    ARCHIVE_EXT = 'tar.gz'
    EXEEXT = ''
if args.bin == Bin.RV64:
    ARCHIVE_SNIP = '-riscv64-linux-gnu.tar.gz'
    ARCHIVE_RE = 'bitcoin-[a-f0-9]+-riscv64-linux-gnu(-debug)?\.tar\.gz'
    ARCHIVE_EXT = 'tar.gz'
    EXEEXT = ''
if args.bin == Bin.WIN:
    ARCHIVE_SNIP = '-win64.zip'
    ARCHIVE_RE = 'bitcoin-[a-f0-9]+-win64\.zip'
    ARCHIVE_EXT = 'zip'
    EXEEXT = '.exe'


def get_lines(url):
    return urllib.request.urlopen(url).read().decode('utf-8').splitlines()


def main():
    root_folder = os.path.abspath(os.path.dirname(__file__))
    src_dir = os.path.normpath(args.srcdir.replace('/c/Users/', 'C:\\Users\\'))

    print(os.getenv('PYTHONIOENCODING'))
    print(sys.stdin.encoding)
    print(sys.stdout.encoding)
    assert 'UTF-8'.lower() == sys.stdin.encoding.lower() == sys.stdout.encoding.lower()
    print(src_dir)
    assert os.path.isdir(src_dir)  # Make sure to git clone bitcoin-core
    import zmq  #noqa

    for line in get_lines(LATEST_URL):
        if 'embed-responsive-item' in line:
            build_id = int(re.sub('^.*builds/([0-9]+)/.*$', '\g<1>', line.strip()))
            break
    print('build id: {}'.format(build_id))

    for line in get_lines(BUILD_URL.format(build_id, '')):
        if ARCHIVE_SNIP in line:
            archive_gitian_name = re.sub('^.*({}).*$'.format(ARCHIVE_RE), '\g<1>', line.strip())
    print('filename: {}'.format(archive_gitian_name))
    version = re.sub('bitcoin-([a-f0-9]+)-.*', '\g<1>', archive_gitian_name)
    print('version: {}'.format(version))

    archive_name = 'bitcoin-core-nightly.{}'.format(ARCHIVE_EXT)
    with open(archive_name, 'wb') as archive:
        archive.write(urllib.request.urlopen(BUILD_URL.format(build_id, archive_gitian_name)).read())

    build_dir = os.path.join(root_folder, 'build_dir')
    shutil.unpack_archive(archive_name, build_dir)
    build_dir = os.path.join(build_dir, 'bitcoin-{}'.format(version), '')

    build_dir_src = os.path.join(build_dir, 'src')
    shutil.rmtree(build_dir_src, ignore_errors=True)
    os.rename(src=os.path.join(build_dir, 'bin'), dst=build_dir_src)
    config_file = os.path.join(src_dir, 'test', 'config.ini')
    shutil.copyfile(os.path.join(root_folder, 'config.ini'), config_file)
    with open(config_file) as f:
        c = f.read() \
        .replace('__BUILDDIR__', build_dir) \
        .replace('__SRCDIR__', src_dir) \
        .replace('__EXEEXT__', EXEEXT)
    with open(config_file, 'w') as f:
        f.write(c)

    with open('build_dir.txt', 'w') as f:
        f.write(build_dir)

    with open('version.txt', 'w') as f:
        f.write(version)


if __name__ == "__main__":
    main()
