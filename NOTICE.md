# NOTICE

This project is licensed under the MIT License (see `LICENSE`).

## Third-party material

The eight style presets in `skills/wechat-mp-studio/scripts/presets.py`
(friendly, notebook, bookish, magazine, news, docs, vivid, bauhaus) including their
color schemes, the palette-derivation approach, and the design of the
`lead / stat / quote-card / compare / steps / checklist` components in `convert.py`
are adapted from **aiworkskills/wechat-article-skills**
(https://github.com/aiworkskills/wechat-article-skills), licensed under the
Apache License, Version 2.0 (http://www.apache.org/licenses/LICENSE-2.0).

Modifications: rewritten as Python style dictionaries generating inline CSS;
removed `background-clip:text` gradient text (stripped by the WeChat editor);
added standalone h2 decorations; list and component rendering reimplemented.
