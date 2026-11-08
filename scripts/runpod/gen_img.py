import torch, json
from diffusers import StableDiffusionXLPipeline
p=StableDiffusionXLPipeline.from_pretrained('stabilityai/stable-diffusion-xl-base-1.0',torch_dtype=torch.float16 if False else torch.float32 if False else torch.bfloat16 if False else torch.float16,variant='fp16').to('cuda')
ITEMS=json.load(open('/root/items.json'))
neg='text, logo, brand, label, watermark, hands, people, cropped, multiple objects, background clutter, shadow'
import os; os.makedirs('/root/img',exist_ok=True)
for k,pr in ITEMS.items():
    for s in range(4):
        im=p(pr+', single object, centered, full object visible, 3/4 view, plain white background, studio product photo, sharp focus, soft even lighting, photorealistic',negative_prompt=neg,num_inference_steps=34,guidance_scale=6.5,height=1024,width=1024,generator=torch.Generator('cuda').manual_seed(100+s)).images[0]
        im.save(f'/root/img/{k}_{s}.png')
    print('img',k,flush=True)
print('IMG_DONE')
