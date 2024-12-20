import gradio as gr
import numpy as np
import random
import torch
from diffusers import DiffusionPipeline

# Configuration
dtype = torch.bfloat16
device = "cuda" if torch.cuda.is_available() else "cpu"

pipe = DiffusionPipeline.from_pretrained("black-forest-labs/FLUX.1-schnell", torch_dtype=dtype).to(device)

MAX_SEED = np.iinfo(np.int32).max
MAX_IMAGE_SIZE = 2048

def infer(
    prompt, 
    seed=42, 
    randomize_seed=False, 
    width=1024, 
    height=1024, 
    num_inference_steps=4, 
    num_samples=3, 
    progress=gr.Progress(track_tqdm=True)
):
    current_seed = seed

    if randomize_seed:
        current_seed = random.randint(0, MAX_SEED)

    generator = torch.Generator().manual_seed(current_seed)
    
    images = pipe(
        prompt=prompt,
        width=width,
        height=height,
        num_inference_steps=num_inference_steps,
        generator=generator,
        guidance_scale=0.0,
        num_images_per_prompt=num_samples or 1
    ).images

    
    # Return an array of images
    return images

examples = [
    "a tiny astronaut hatching from an egg on the moon",
    "a cat holding a sign that says hello world",
    "an anime illustration of a wiener schnitzel",
]

css = """
#col-container {
    margin: 0 auto;
    max-width: 520px;
}
"""

# Gradio interface
with gr.Blocks(css=css) as demo:
    with gr.Column(elem_id="col-container"):
        gr.Markdown("""
        # FLUX.1 [schnell]
        12B param rectified flow transformer distilled from [FLUX.1 [pro]](https://blackforestlabs.ai/) for 4 step generation
        [[blog](https://blackforestlabs.ai/announcing-black-forest-labs/)] [[model](https://huggingface.co/black-forest-labs/FLUX.1-schnell)]
        """)

        with gr.Row():
            prompt = gr.Text(
                label="Prompt",
                show_label=False,
                max_lines=1,
                placeholder="Enter your prompt",
                container=False,
            )
            run_button = gr.Button("Run", scale=0)
        
        # Corrected Gallery component: No .style(), use "columns" directly
        result_gallery = gr.Gallery(label="Results", columns=[4], height="auto")
        seeds_text = gr.Text(label="Seeds Used", interactive=False)

        with gr.Accordion("Advanced Settings", open=False):
            seed = gr.Slider(
                label="Seed",
                minimum=0,
                maximum=MAX_SEED,
                step=1,
                value=0,
            )
            randomize_seed = gr.Checkbox(label="Randomize seed", value=True)

            with gr.Row():
                width = gr.Slider(
                    label="Width",
                    minimum=256,
                    maximum=MAX_IMAGE_SIZE,
                    step=32,
                    value=1024,
                )
                height = gr.Slider(
                    label="Height",
                    minimum=256,
                    maximum=MAX_IMAGE_SIZE,
                    step=32,
                    value=1024,
                )
            
            with gr.Row():
                num_inference_steps = gr.Slider(
                    label="Number of inference steps",
                    minimum=1,
                    maximum=50,
                    step=1,
                    value=4,
                )
                
                # Add a parameter to specify how many samples to generate
                num_samples = gr.Slider(
                    label="Number of samples",
                    minimum=1,
                    maximum=10,
                    step=1,
                    value=3,
                )

        gr.Examples(
            examples=examples,
            fn=infer,
            inputs=[prompt],
            outputs=[result_gallery, seeds_text],
            cache_examples="lazy"
        )

    # Trigger inference with prompt submission or button click
    run_button.click(
        fn=infer,
        inputs=[prompt, seed, randomize_seed, width, height, num_inference_steps, num_samples],
        outputs=[result_gallery, seeds_text]
    )
    prompt.submit(
        fn=infer,
        inputs=[prompt, seed, randomize_seed, width, height, num_inference_steps, num_samples],
        outputs=[result_gallery, seeds_text]
    )

demo.launch(share=True)
