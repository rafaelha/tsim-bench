"""List or extract members of a remote zip archive using HTTP range requests.

Zenodo's ``/api/records/<id>/files/<name>/content`` endpoint honours ``Range`` headers, so only the
central directory and the requested members are downloaded.

Usage:
    python tools/remote_zip.py URL                      # list members
    python tools/remote_zip.py URL OUT_DIR REGEX        # extract members whose name matches REGEX
"""

import io
import pathlib
import re
import sys
import urllib.request
import zipfile


class HTTPRangeFile(io.RawIOBase):
    def __init__(self, url):
        self.url = url
        self.pos = 0
        request = urllib.request.Request(url, headers={"Range": "bytes=0-0"})
        with urllib.request.urlopen(request) as response:
            self.size = int(response.headers["Content-Range"].rsplit("/", 1)[1])

    def seekable(self):
        return True

    def readable(self):
        return True

    def tell(self):
        return self.pos

    def seek(self, offset, whence=io.SEEK_SET):
        base = {io.SEEK_SET: 0, io.SEEK_CUR: self.pos, io.SEEK_END: self.size}[whence]
        self.pos = base + offset
        return self.pos

    def read(self, n=-1):
        if n is None or n < 0:
            n = self.size - self.pos
        if n == 0 or self.pos >= self.size:
            return b""
        end = min(self.pos + n, self.size) - 1
        request = urllib.request.Request(self.url, headers={"Range": f"bytes={self.pos}-{end}"})
        with urllib.request.urlopen(request) as response:
            data = response.read()
        self.pos += len(data)
        return data

    def readinto(self, buffer):
        data = self.read(len(buffer))
        buffer[: len(data)] = data
        return len(data)


def open_remote_zip(url):
    return zipfile.ZipFile(io.BufferedReader(HTTPRangeFile(url), buffer_size=1 << 20))


def main():
    archive = open_remote_zip(sys.argv[1])
    if len(sys.argv) == 2:
        for info in archive.infolist():
            print(info.file_size, info.filename)
        return
    out, pattern = pathlib.Path(sys.argv[2]), re.compile(sys.argv[3])
    for info in archive.infolist():
        if pattern.search(info.filename) and not info.is_dir():
            target = out / info.filename
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(archive.read(info))
            print("extracted", info.filename, info.file_size)


if __name__ == "__main__":
    main()
