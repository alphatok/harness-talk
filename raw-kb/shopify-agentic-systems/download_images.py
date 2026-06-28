import asyncio
import httpx
import os

IMAGES = [
    ("image_01_robot_judge", "https://cdn.shopify.com/s/files/1/0779/4361/articles/image_1_02f5ef22-dd8c-4717-91cb-070b71b0c679.png?v=1759988609&originalWidth=1848&originalHeight=782"),
    ("image_02_agentic_loop", "https://cdn.shopify.com/s/files/1/0779/4361/files/agenticloop_ecdd37d0-0dd2-4171-ba5a-0cda8a79c003.png?v=1755211658"),
    ("image_03_segmentation", "https://cdn.shopify.com/s/files/1/0779/4361/files/segmentation.png?v=1755211701"),
    ("image_04_tool_complexity", "https://cdn.shopify.com/s/files/1/0779/4361/files/toolcomplexity.png?v=1755211760"),
    ("image_05_death_by_instructions", "https://cdn.shopify.com/s/files/1/0779/4361/files/deathbyathousandinstructions.png?v=1755211795"),
    ("image_06_prompt", "https://cdn.shopify.com/s/files/1/0779/4361/files/prompt.png?v=1755212586"),
    ("image_07_vibe_test", "https://cdn.shopify.com/s/files/1/0779/4361/files/Vibetest.png?v=1755213228"),
    ("image_08_sidekick_error", "https://cdn.shopify.com/s/files/1/0779/4361/files/sidekickerror.png?v=1755213874"),
    ("image_09_ground_truth_set", "https://cdn.shopify.com/s/files/1/0779/4361/files/groundtruthset.png?v=1755213948"),
    ("image_10_evaluation", "https://cdn.shopify.com/s/files/1/0779/4361/files/evaluation.png?v=1755214576"),
    ("image_11_llm_judge", "https://cdn.shopify.com/s/files/1/0779/4361/files/LLMjudge.png?v=1755214642"),
    ("image_12_robot", "https://cdn.shopify.com/s/files/1/0779/4361/files/robot.png?v=1755216341"),
    ("image_13_evaluation_pipeline", "https://cdn.shopify.com/s/files/1/0779/4361/files/Evaluationpipeline.png?v=1755216366"),
    ("image_14_grpo", "https://cdn.shopify.com/s/files/1/0779/4361/files/GRPO.png?v=1755216699"),
]

async def download_image(client: httpx.AsyncClient, name: str, url: str, output_dir: str) -> bool:
    output_path = os.path.join(output_dir, f"{name}.png")
    
    if os.path.exists(output_path):
        print(f"Exists: {name}.png")
        return True
    
    try:
        response = await client.get(url, timeout=30)
        response.raise_for_status()
        with open(output_path, "wb") as f:
            f.write(response.content)
        print(f"Downloaded: {name}.png")
        return True
    except Exception as e:
        print(f"Failed: {name} - {e}")
        return False

async def main():
    output_dir = os.path.dirname(os.path.abspath(__file__))
    
    async with httpx.AsyncClient() as client:
        tasks = [download_image(client, name, url, output_dir) for name, url in IMAGES]
        await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(main())