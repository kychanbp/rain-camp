cd /root
apt-get update -qq >/dev/null; apt-get install -y -qq git git-lfs libgl1 libglib2.0-0 libegl1 ffmpeg build-essential cmake >/dev/null
git clone -q --recursive https://github.com/Tencent-Hunyuan/HY-World-2.0 hy
cd hy
python -m venv /root/ve --system-site-packages; . /root/ve/bin/activate
pip -q install -U pip wheel setuptools 2>&1 | tail -1
pip -q install torch==2.7.1 torchvision==0.22.1 torchaudio==2.7.1 --index-url https://download.pytorch.org/whl/cu126 2>&1 | tail -1
pip -q install -r requirements.txt 2>&1 | tail -2
cd hyworld2/worldgen/third_party/gsplat_maskgaussian && pip -q install -e . --no-build-isolation 2>&1 | tail -1; cd /root/hy
pip -q install flash-attn --no-build-isolation 2>&1 | tail -1
pip -q install --no-build-isolation -r requirements_git.txt 2>&1 | tail -1
cd hyworld2/worldgen/third_party/navmesh && pip -q install . --no-build-isolation 2>&1 | tail -1; cd /root/hy
pip -q install -r hyworld2/panogen/requirements.txt 2>&1 | tail -1
pip -q install vllm 2>&1 | tail -1
echo W_DONE
python -c "import torch;print(torch.__version__,torch.cuda.is_available())"
