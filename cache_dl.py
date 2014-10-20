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

    def __init__(self, cachedir=None, packet_size=1204, *,
                 use_default_bar=False):
        """Ensures that cachedir() and cachedir('cache.json') both exist,
        then loads cache info from cachedir('cache.json')"""
        sysname = os.uname().sysname
        sysname = sysname if sysname in self.SYSTEM_CACHEDIRS else '_other_'
        self._cachedir_ = (cachedir if cachedir is not None
                           else self.SYSTEM_CACHEDIRS[sysname])

        self._packet_size_ = packet_size

        if use_default_bar:
            self.before_dl = self._default_bar_before_dl_
            self.each_packet = self._default_bar_each_packet_
            self.length_error = self._default_bar_length_error_
            self.after_dl = self._default_bar_after_dl_

        os.makedirs(self.cachedir(), exist_ok=True)
        if not os.path.exists(self.cachedir('cache.json')):
            with open(self.cachedir('cache.json'), 'w') as wf:
                wf.write('{}')
        self._load_cache_()

    def _load_cache_(self):
        """Loads cache info from cachedir('cache.json')"""
        with open(self.cachedir('cache.json')) as rf:
            self._cache_ = json.loads(rf.read())

    def _save_cache_(self):
        """Saves cache info to cachedir('cache.json')"""
        with open(self.cachedir('cache.json'), 'w') as wf:
            wf.write(json.dumps(self._cache_))

    def cachedir(self, *args):
        """Get a directory relative to ~/.cdlcache
        :param args: Passed directly to os.path.join
        """
        return os.path.join(self._cachedir_, *args)

    def _curl_(self, url, dst):
        """Download the content of url and save it to dst
        :param url: Where to download from
        :param dst: Where to download to
        """
        with open(dst, 'wb') as wf:
            self.before_dl(url, dst)
            resp = urlopen(url)
            length = resp.getheader('Content-Length')
            if length is None:
                self.length_error(resp)
                wf.write(resp.read())
            else:
                dlbytes = 0
                length = int(length)
                while dlbytes < length:
                    dlbytes += self._packet_size_
                    wf.write(resp.read(self._packet_size_))
                    pct = int(100 * dlbytes / length)
                    self.each_packet(dlbytes, length, pct)
                self.after_dl(url, dst, length)

    def before_dl(self, url, dst):
        pass

    def each_packet(self, bytec, out_of, pct):
        pass

    def length_error(self, resp):
        pass

    def after_dl(self, url, dst, total):
        pass

    def _default_bar_before_dl_(self, url, dst):
        print("'{}' -> '{}'".format(url, dst))

    def _default_bar_each_packet_(self, bytec, out_of, pct):
        barcount = int(pct/2)
        print('\r[{}{}] ({}%)'.format(
            '=' * barcount, ' ' * (50 - barcount), pct
        ), end='')

    def _default_bar_length_error_(self, resp):
        print("  Can't get a length, no progress bar")

    def _default_bar_after_dl_(self, url, dst, total):
        print()

    def _dl_from_cache_(self, url):
        """Get a file from cachedir(), based on url and cache info"""
        return self.cachedir(self._cache_[url]['id'])

    def _dl_to_cache(self, url):
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
        self._curl_(url, self.cachedir(fname))
        self._cache_[url] = cached
        self._save_cache_()
        return self._dl_from_cache_(url)

    def _dl_check_cache(self, url):
        """Checks whether or not the url is in the cache.
        Doesn't do any server checking."""
        if url in self._cache_:
            return self._dl_from_cache_(url)
        else:
            return self._dl_to_cache(url)

    def _dl_check_head_(self, url):
        """Checks whether or not the resource has been updated on the server."""
        cached = self._cache_[url] if url in self._cache_ else None
        req = Request(url)
        if cached is None:
            return self._dl_to_cache(url)
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
            return self._dl_to_cache(url)

    def get(self, url, *, check_head=True, check_cache=True):
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
                return self._dl_check_head_(url)
            else:
                return self._dl_check_cache(url)
        else:
            return self._dl_to_cache(url)
