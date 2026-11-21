# wechat-mp-studio

## Keep README screenshots current

`docs/images/preview.png` is generated, not hand-made. Whenever a change touches the preview UI
(`skills/wechat-mp-studio/scripts/preview.py`), theme rendering (`convert.py`, `themes.py`, `presets.py`)
or `examples/hello/article.md`, regenerate it in the same commit:

```
python3 tools/screenshot_preview.py   # needs: pip install playwright pillow && playwright install chromium
```

Look at the resulting image before committing, and update the README feature bullets (both `README.md`
and `README.en.md`) if the UI gained or lost a feature.
