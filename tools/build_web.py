"""Package the unchanged project into size-bounded, cacheable asset archives."""
import hashlib
import json
import os
import re
from pathlib import Path
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app"
DIST = ROOT / "dist"
MAX_RAW = 16 * 1024 * 1024


def package():
    manifest = DIST / "asset-packs.json"
    previous = json.loads(manifest.read_text())["packs"] if manifest.exists() else []
    paths = sorted(p for p in APP.rglob("*") if p.is_file()
                   and "__pycache__" not in p.parts and p.suffix != ".pyc")
    groups, group, size = [], [], 0
    for path in paths:
        if group and size + path.stat().st_size > MAX_RAW:
            groups.append(group)
            group, size = [], 0
        group.append(path)
        size += path.stat().st_size
    if group:
        groups.append(group)
    packs = []
    for index, group in enumerate(groups):
        digest = hashlib.sha256()
        for path in group:
            digest.update(path.relative_to(APP).as_posix().encode())
            digest.update(path.read_bytes())
        name = f"game-{index + 1}-{digest.hexdigest()[:12]}.zip"
        target = DIST / name
        with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
            for path in group:
                archive.write(path, "assets/" + path.relative_to(APP).as_posix())
        assert target.stat().st_size < 25 * 1024 * 1024
        packs.append({"url": name, "bytes": target.stat().st_size,
                      "sha256": hashlib.sha256(target.read_bytes()).hexdigest()})
    manifest.write_text(json.dumps({"packs": packs, "files": len(paths)}, indent=2))
    current = {p['url'] for p in packs}
    for pack in previous:
        name = pack['url']
        if name not in current and re.fullmatch(r"game-\d+-[a-f0-9]{12}\.zip", name):
            (DIST / name).unlink(missing_ok=True)
    print(f"Packed {len(paths)} files, {len(packs)} archives, {sum(p['bytes'] for p in packs)/1024/1024:.1f} MiB")


def export_interface_assets():
    # Render existing game surfaces verbatim for optional large touch controls.
    # No portraits, sprites, animation frames or gameplay assets are redrawn.
    os.environ["SDL_VIDEODRIVER"] = "dummy"
    os.environ["SDL_AUDIODRIVER"] = "dummy"
    sys.path.insert(0, str(APP))
    import pygame as pg
    pg.init()
    from source import constants as c, tool
    from source.component.pvz_ui import paper_panel
    (DIST / "cards").mkdir(exist_ok=True)
    for _, key, _, _ in c.PLANT_CARD_INFO:
        pg.image.save(tool.GFX[key], DIST / "cards" / f"{key}.png")
    # Cover actors are verbatim game frames, not AI reinterpretations of faces.
    # Keep separate transparent images so layout cannot redraw facial features.
    actors = {'sun': c.GASSUNFLOWER, 'nut': c.PORTRAITTALLNUT,
              'shooter': c.GRINDEVOURER, 'chomper': c.PORTRAITCHOMPER,
              'zombie': c.PORTRAIT_ZOMBIE, 'elite': c.ELITE_PORTRAIT_ZOMBIE}
    (DIST / 'cover-actors').mkdir(exist_ok=True)
    for label, key in actors.items():
        frame = tool.GFX[key][0]
        target = DIST / 'cover-actors' / f'{label}.png'
        pg.image.save(frame, target)
        assert pg.image.tobytes(pg.image.load(target), 'RGBA') == pg.image.tobytes(frame, 'RGBA')
    pg.image.save(tool.GFX[c.UNIVERSAL_BUTTON], DIST / "button.png")
    pg.image.save(paper_panel((548, 265)), DIST / "paper.png")
    pg.image.save(pg.image.load(APP / "pypvz-exec-logo.png"), DIST / "favicon.png")
    pg.quit()


if __name__ == "__main__":
    export_interface_assets()
    package()
