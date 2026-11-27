"""Find a browser to render with: the person's Chrome or Edge first, then Playwright's own Chromium."""
import glob, os

ARGS = ['--allow-file-access-from-files', '--force-color-profile=srgb', '--font-render-hinting=none']


def launch(p):
    for ch in ('chrome', 'msedge', None):
        try:
            return p.chromium.launch(channel=ch, args=ARGS) if ch else p.chromium.launch(args=ARGS)
        except Exception:
            pass
    paths = [os.environ.get('STUDIO_CHROME', '')] + sorted(glob.glob('/opt/pw-browsers/chromium-*/chrome-linux*/chrome'))
    for exe in paths:
        if exe and os.path.exists(exe):
            return p.chromium.launch(executable_path=exe, args=ARGS)
    raise RuntimeError('NEED_BROWSER')


if __name__ == '__main__':
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        try:
            launch(p).close(); print('READY')
        except Exception:
            print('NEED_BROWSER')
