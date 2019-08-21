CNX to REX library/utility
==========================

This library and utility provides logic
for creating REX book redirects from CNX to OpenStax.

The scope of this library is providing logic that
redirects CNX users to OpenStax (REX feature).


Installation
------------

Requires Python >= 3.7

Via PyPI::

  pip install cnx-rex-redirects

Usage
-----

Usage help::

  rex_redirect --help

Example usage::

  rex_redirects --openstax-host staging.openstax.org --archive-host archive-staging.cnx.org -o - generate-cnx-uris-for-rex-books > uris.txt

License
-------

This software is subject to the provisions of the GNU Affero General
Public License Version 3.0 (AGPL). See license.txt for details.
Copyright (c) 2019 Rice University
