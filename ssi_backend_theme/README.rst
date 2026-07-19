.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

==============
Backend Theme
==============

This module defines a "Backend Theme" master data model, used to manage a
set of reusable backend UI theme presets (brand color palette and
typography) that a deployment can pick from without touching code.

Each theme preset stores optional brand colors (primary, navbar background,
navbar text), typography (font family, base font size), and defaults for
sidebar state and color scheme.

An administrator can designate one theme preset as the active backend theme
from *Settings*. Once selected, its font is applied live as a CSS custom
property after the browser reloads. Its primary and navbar background
colors take effect after the backend assets are recompiled (which happens
automatically as part of picking the active theme) since Odoo/Bootstrap
compute several derived shades from them at asset-compile time. If no
theme is active, or the active one is deleted or archived, the backend
falls back to the default look.


Installation
============

To install this module, you need to:

1.  Clone the branch 19.0 of the repository https://github.com/open-synergy/ssi-backend-theme
2.  Add the path to this repository in your configuration (addons-path)
3.  Update the module list (Must be on developer mode)
4.  Go to menu *Apps -> Apps -> Main Apps*
5.  Search For *Backend Theme*
6.  Install the module


Bug Tracker
===========

Bugs are tracked on `GitHub Issues
<https://github.com/open-synergy/ssi-backend-theme/issues>`_. In case of trouble, please
check there if your issue has already been reported. If you spotted it first,
help us smash it by providing detailed and welcomed feedback.


Credits
=======

Contributors
------------

* Andhitia Rama <andhitia.r@gmail.com>

Maintainer
----------

.. image:: https://simetri-sinergi.id/logo.png
   :alt: PT. Simetri Sinergi Indonesia
   :target: https://simetri-sinergi.id

This module is maintained by the PT. Simetri Sinergi Indonesia.
