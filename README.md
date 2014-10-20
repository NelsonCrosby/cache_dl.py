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
