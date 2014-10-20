import os
import json
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from uuid import uuid4


class CachedDownloader:
    """A downloader that can cache a server's response in ~/.cdlcache
    Written by Nelson Crosby <nc@sourcecomb.com> (github/NelsonCrosby).
    Copyright (c) 2014 Nelson Crosby
    Licensed under the MIT license.
    See https://github.com/NelsonCrosby/cache_dl.py for more info."""
    SYSTEM_CACHEDIRS = {
        'Windows': os.path.expanduser(
            os.path.join('~', 'AppData', 'Roaming', 'cdlcache')
        ),
        'Mac': os.path.expanduser(
            os.path.join('~', 'Application Support', 'cdlcache')
        ),
        '_other_': os.path.expanduser(os.path.join('~', '.cdlcache'))
    }

    @staticmethod
    def _curl_(url, dst, *, echo=False):
        """Download the content of url and save it to dst
        :param url: Where to download from
        :param dst: Where to download to
        :param echo: If True, use a progress bar. Defaults to False.
        """
        with open(dst, 'wb') as wf:
            if echo:
                print("'{}' -> '{}'".format(url, dst))
            resp = urlopen(url)
            length = resp.getheader('Content-Length')
            if length is None:
                print("  Can't get a length, no progress bar")
                wf.write(resp.read())
            else:
                dlbytes = 0
                length = int(length)
                while dlbytes < length:
                    dlbytes += 1
                    wf.write(resp.read(1))
                    pct = int(100 * dlbytes / length)
                    barcount = int(pct / 2)
                    if echo:
                        print('\r[{}{}] ({}%)'.format(
                            '=' * barcount, ' ' * (50 - barcount), pct
                        ), end='')
                if echo:
                    print()

    def __init__(self, cachedir=None):
        """Ensures that cachedir() and cachedir('cache.json') both exist,
        then loads cache info from cachedir('cache.json')"""
        sysname = os.uname().sysname
        sysname = sysname if sysname in self.SYSTEM_CACHEDIRS else '_other_'
        self._cachedir_ = (cachedir if cachedir is not None
                           else self.SYSTEM_CACHEDIRS[sysname])

        os.makedirs(self.cachedir(), exist_ok=True)
        if not os.path.exists(self.cachedir('cache.json')):
            with open(self.cachedir('cache.json'), 'w') as wf:
                wf.write('{}')
        self._load_cache_()

    def cachedir(self, *args):
        """Get a directory relative to ~/.cdlcache
        :param args: Passed directly to os.path.join
        """
        return os.path.join(self._cachedir_, *args)

    def _load_cache_(self):
        """Loads cache info from cachedir('cache.json')"""
        with open(self.cachedir('cache.json')) as rf:
            self._cache_ = json.loads(rf.read())

    def _save_cache_(self):
        """Saves cache info to cachedir('cache.json')"""
        with open(self.cachedir('cache.json'), 'w') as wf:
            wf.write(json.dumps(self._cache_))

    def _dl_from_cache_(self, url):
        """Get a file from cachedir(), based on url and cache info"""
        return self.cachedir(self._cache_[url]['id'])

    def _dl_to_cache(self, url, *, progress=True):
        """Downloads a file and stores it in cachedir().
        Doesn't do any existence or redundancy checking."""
        fname = uuid4().urn[9:]
        cached = {'id': fname}
        req = Request(url)
        req.method = 'HEAD'
        resp = urlopen(req)
        lastmod = resp.getheader('Last-Modified')
        etag = resp.getheader('ETag')
        if lastmod is not None:
            cached['last-modified'] = lastmod
        elif etag is not None:
            cached['etag'] = etag
        self._curl_(url, self.cachedir(fname), echo=progress)
        self._cache_[url] = cached
        self._save_cache_()
        return self._dl_from_cache_(url)

    def _dl_check_cache(self, url, *, progress=True):
        """Checks whether or not the url is in the cache.
        Doesn't do any server checking."""
        if url in self._cache_:
            return self._dl_from_cache_(url)
        else:
            return self._dl_to_cache(url, progress=progress)

    def _dl_check_head_(self, url, *, progress=True):
        """Checks whether or not the resource has been updated on the server."""
        cached = self._cache_[url] if url in self._cache_ else None
        req = Request(url)
        if cached is None:
            return self._dl_to_cache(url, progress=progress)
        elif 'etag' in cached:
            req.add_header('If-None-Match', cached['etag'])
        elif 'last-modified' in cached:
            req.add_header('If-Modified-Since', cached['last-modified'])
        else:
            return self._dl_from_cache_(url)
        try:
            resp = urlopen(req)
        except HTTPError as e:
            if e.code == 304:
                return self._dl_from_cache_(url)
        else:
            return self._dl_to_cache(url, progress=progress)

    def get(self, url, *, progress=True, check_head=True, check_cache=True):
        """The method that drives it all.
        If progress is True, displays a progress bar if necessary.
        If check_cache is False, forces downloading of the resource.
        If check_cache is True, check_head is False, and the resource exists in
         cachedir(), don't download. If it doesn't exist, download and store it.
        If check_cache is True, check_head is True, and the resource exists in
         cachedir(), check if there has been an update before downloading.
        :returns The filename of the downloaded resource. NOTE: the filename
         _does not_ have a file extension, so don't rely on that.
        """
        if check_cache:
            if check_head:
                return self._dl_check_head_(url, progress=progress)
            else:
                return self._dl_check_cache(url, progress=progress)
        else:
            return self._dl_to_cache(url, progress=progress)
