"""Download CC0 textures, HDRIs and models from Poly Haven into data/."""
import json, os, sys, urllib.request, concurrent.futures as cf
OUT = os.path.join(os.path.dirname(__file__), '..', 'data')
UA = {'User-Agent': 'rain-camp-personal/0.1'}
TEX = "forest_ground_04 forest_leaves_04 forest_leaves_02 pine_bark grass_path_2 brown_mud_leaves_01 fabric_leather_02 aerial_grass_rock".split()
HDRI = "misty_pines kloofendal_overcast_puresky".split()
MODELS = """pine_sapling_medium pine_sapling_small pine_roots dead_tree_trunk dry_branches_medium_01 tree_stump_02
food_avocado_01 wooden_cutting_board pot_enamel_01 Lantern_01 modified_thermos wooden_bowl_02 yellow_onion folding_wooden_stool hatchet plastic_jerrycan rubber_boots""".split()
def get(url, path):
    if os.path.exists(path): return
    os.makedirs(os.path.dirname(path), exist_ok=True)
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=300) as r, open(path + '.tmp', 'wb') as f: f.write(r.read())
    os.rename(path + '.tmp', path)
def info(a): return json.load(urllib.request.urlopen(urllib.request.Request(f'https://api.polyhaven.com/files/{a}', headers=UA), timeout=30))
def tex(a):
    d = info(a); got = []
    for key, fn in (('Diffuse', 'c'), ('nor_gl', 'n'), ('Rough', 'r'), ('AO', 'a'), ('Displacement','d')):
        if key not in d: continue
        e = d[key].get('2k', {}); j = e.get('jpg') or e.get('png')
        if j: get(j['url'], f"{OUT}/tex/{a}_{fn}.jpg"); got.append(fn)
    return a, got
def hdri(a):
    d = info(a); get(d['hdri']['2k']['hdr']['url'], f'{OUT}/hdri/{a}.hdr'); return a, 'ok'
def model(a):
    d = info(a); e = d['gltf']['1k']['gltf']; size = e.get('size', 0)
    get(e['url'], f'{OUT}/models/{a}/{a}.gltf')
    for rel, v in e.get('include', {}).items(): get(v['url'], f'{OUT}/models/{a}/{rel}')
    return a, size // 1000000
with cf.ThreadPoolExecutor(6) as ex:
    fs = [ex.submit(tex, a) for a in TEX] + [ex.submit(hdri, a) for a in HDRI] + [ex.submit(model, a) for a in MODELS]
    for f in cf.as_completed(fs):
        try: print(f.result(), flush=True)
        except Exception as e: print('ERR', e, flush=True)
