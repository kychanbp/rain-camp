set -e
cd /workspace 2>/dev/null || cd /root
apt-get update -qq >/dev/null; apt-get install -y -qq libgl1 libglib2.0-0 git >/dev/null
git clone -q --depth 1 https://github.com/Tencent/Hunyuan3D-2.git h3d
cd h3d
pip -q install -r requirements.txt 2>&1 | tail -1
pip -q install -e . 2>&1 | tail -1
cd hy3dgen/texgen/custom_rasterizer && pip -q install -e . 2>&1 | tail -1; cd ../../..
cd hy3dgen/texgen/differentiable_renderer && bash compile_mesh_painter.sh 2>&1 | tail -1; cd ../../..
pip -q install diffusers transformers accelerate sentencepiece 2>&1 | tail -1
echo SETUP_DONE
