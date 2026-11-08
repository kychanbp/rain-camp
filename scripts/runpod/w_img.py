import torch
from diffusers import StableDiffusionXLPipeline
p=StableDiffusionXLPipeline.from_pretrained('stabilityai/stable-diffusion-xl-base-1.0',torch_dtype=torch.float16,variant='fp16').to('cuda')
pr='wide landscape photo inside a tall slash pine forest in steady rain, overcast, misty, straight trunks, ground carpeted with rust red fallen pine needles, patches of wet green grass in a clearing, young pine saplings with long needles, nature photography, realistic, natural light, empty forest'
neg='people, tent, car, building, text, watermark, painting, cartoon'
for s in range(4):
    p(pr,negative_prompt=neg,num_inference_steps=36,guidance_scale=6,width=1344,height=768,generator=torch.Generator('cuda').manual_seed(40+s)).images[0].save(f'/root/f{s}.png')
print('IMG_DONE')
