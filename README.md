# Rain Camp

A rainy night in a pine forest with two dogs. Your breath does the work: each slow breath raises the tent, lights the lamps and cooks the meal. There is nothing to win and no way to lose. Runs in a browser on desktop, phone and Meta Quest. English and Simplified Chinese.

The world is an original camp. It takes its idea from rainy camping videos but uses no footage, branding or real people.

## Run

    python3 scripts/serve.py 8000

Open http://localhost:8000.

## Build

1. `scripts/fetch_assets.py` gets CC0 assets from Poly Haven into data/.
2. `scripts/make_world.py` plans the ground and trees.
3. `scripts/cluster_trees.py`, `blender/make_trees.py`, `scripts/pack_trees.py` make the pines.
4. `blender/build_camp.py` builds the tent, car and gear in Blender and bakes light. `scripts/pack_camp.py` packs the result.
5. `scripts/gen_tex.py`, `scripts/make_dogs.py`, `scripts/make_audio.py` make textures, dogs and sound.

## Credits

Trees, some props and textures: Poly Haven (CC0). All sound is synthesised. three.js (MIT).
