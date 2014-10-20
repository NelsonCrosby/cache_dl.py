# cache_dl.py - A caching downloader #

Allows re-requesting of HTTP resources, without re-downloading constantly.

Stores all results in `~/.cdlcache`. Each result is given a UUID as a filename,
 which is mapped to by URL in `~/.cdlcache/cache.json`.

This script is not actually supposed to be imported. It will work perfectly
 fine if you do, but the whole point is that the contents of cache_dl.py can be
 copied to the top of your script (for cases where a single script is best). As
 such, cache_dl.py is specifically designed to not have any dependencies
 itself (besides the requirement for Python 3).

If you do copy this script, the docstring for the class `CachedDownloader` MUST
 remain in tact.


## Using ##

Simple. Download cache_dl.py. Either the script contents to the top of your
 working script, or place it somewhere it can be imported.

Create an instance of `CachedDownloader`. The main thing you will have to worry
 about is `CachedDownloader#get(url, *, progress, check_cache, check_head)`.
 That will take care of getting everything for you, just give it your URL and
 get back a path to a file (this file is guaranteed to exist).

`CachedDownloader` also takes three arguments. The first, `cachedir`, tells
 `CachedDownloader` where to put the downlead cache. Usually, this defaults to
 the standard hidden location on your system (e.g. `~/.cachedir` on Linux).
 It is preferred to use the default cachedir, as it might mean less downloads
 where your resources are shared by another script.

The second, `packet_size`, tells the number of bytes to download at a time.
 Defaults to `1024`.

You can also subclass `CachedDownloader` and override some methods to get
 different functionality during download:

- `before_dl(self, url, dst)` is called before the download starts.
- `each_packet(self, bytec, out_of, percent)` is called after each packet is
    downloaded.
- `after_dl(self, url, dst, total_bytes)` is called after the download ends.

The above methods have an optional default - a primitive progress bar displayed
 in the terminal. You can activate these by setting the constructor's keyword
 argument `use_default_bar` to `True`.

You should probably note that `CachedDownloader` doesn't do any validation of
 the URL. It _expects_ that it will be working with an HTTP URL, and doesn't
 do any checking before passing it to `urlopen` (which is designed to be able
 to handle a few other protocols as well, such as FTP). It's up to you to take
 care with that.
