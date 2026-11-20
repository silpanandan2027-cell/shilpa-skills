"""Animate a still into a short clip with the free, open LTX-Video 2B distilled model, on CPU.

Usage: python3 gen.py <clip> <width> <height> <frames> [seed]
  clip   : a key in prompts.json (its image + prompt; embeddings precomputed in embeds.pt)
  frames : 8*k + 1 (e.g. 49, 73, 97)
Writes clip-<clip>-ltx.mp4 next to this file. Model files are in /root/ltx.
"""
import json
import sys
import time

import torch
from PIL import Image
from diffusers import AutoencoderKLLTXVideo, FlowMatchEulerDiscreteScheduler, LTXVideoTransformer3DModel
from diffusers.pipelines.ltx.pipeline_ltx_condition import LTXConditionPipeline, LTXVideoCondition
from diffusers.utils import export_to_video

torch.set_num_threads(4)
name, width, height, frames = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4])
seed = int(sys.argv[5]) if len(sys.argv) > 5 else 3
CKPT = "/root/ltx/ltxv-2b-0.9.8-distilled.safetensors"
BASE = "/root/ltx/base"

cfg = json.load(open("prompts.json"))
emb = torch.load("embeds.pt")
pe, pm = emb[name]

t0 = time.time()
transformer = LTXVideoTransformer3DModel.from_single_file(CKPT, config=BASE, subfolder="transformer", torch_dtype=torch.float32)
vae = AutoencoderKLLTXVideo.from_single_file(CKPT, config=BASE, subfolder="vae", torch_dtype=torch.float32)
scheduler = FlowMatchEulerDiscreteScheduler.from_pretrained(BASE, subfolder="scheduler")
pipe = LTXConditionPipeline(scheduler=scheduler, vae=vae, text_encoder=None, tokenizer=None, transformer=transformer)
vae.enable_tiling()
print(f"loaded in {time.time() - t0:.0f}s", flush=True)

img = Image.open(cfg["clips"][name]["image"]).convert("RGB").resize((width, height), Image.LANCZOS)


def step_log(p, i, t, kw):
    print(f"step {i + 1} done at {time.time() - t0:.0f}s", flush=True)
    return kw


t0 = time.time()
out = pipe(
    conditions=[LTXVideoCondition(image=img, frame_index=0)],
    prompt_embeds=pe,
    prompt_attention_mask=pm,
    width=width,
    height=height,
    num_frames=frames,
    frame_rate=24,
    timesteps=[1000, 993, 987, 981, 975, 909, 725, 0.03],  # the distilled model's 8-step schedule
    guidance_scale=1.0,
    decode_timestep=0.05,
    decode_noise_scale=0.025,
    image_cond_noise_scale=0.0,
    generator=torch.Generator().manual_seed(seed),
    callback_on_step_end=step_log,
    output_type="latent",
).frames
torch.save(out, f"latents-{name}.pt")

# free the 2B transformer before decoding, so the VAE decode fits in memory
import gc
from diffusers.utils.torch_utils import randn_tensor

pipe.transformer = None
del transformer
gc.collect()
latents = pipe._denormalize_latents(out, vae.latents_mean, vae.latents_std, vae.config.scaling_factor)
timestep = None
if vae.config.timestep_conditioning:
    noise = randn_tensor(latents.shape, generator=torch.Generator().manual_seed(seed), dtype=latents.dtype)
    timestep = torch.tensor([0.05], dtype=latents.dtype)
    latents = (1 - 0.025) * latents + 0.025 * noise
with torch.no_grad():
    video = vae.decode(latents, timestep, return_dict=False)[0]
frames = pipe.video_processor.postprocess_video(video, output_type="pil")[0]
export_to_video(frames, f"clip-{name}-ltx.mp4", fps=24)
print(f"wrote clip-{name}-ltx.mp4 in {time.time() - t0:.0f}s", flush=True)
