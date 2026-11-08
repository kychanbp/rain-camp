. /root/ve/bin/activate
pip -q uninstall -y vllm 2>&1 | tail -1
pip -q install torch==2.7.1 torchvision==0.22.1 torchaudio==2.7.1 --index-url https://download.pytorch.org/whl/cu126 2>&1 | tail -1
cd /root/hy; pip -q install -r requirements.txt 2>&1 | tail -1
python -c "import torch,transformers,diffusers,gsplat;print(torch.__version__,transformers.__version__,diffusers.__version__)"
echo ENV_DONE
deactivate
python -m venv /root/ve3; . /root/ve3/bin/activate; pip -q install vllm 2>&1 | tail -1; echo VLLM_DONE
