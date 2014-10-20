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

You should probably note that `CachedDownloader` doesn't do any validation of
 the URL. It _expects_ that it will be working with an HTTP URL, and doesn't
 do any checking before passing it to `urlopen` (which is designed to be able
 to handle a few other protocols as well, such as FTP). It's up to you to take
 care with that.
