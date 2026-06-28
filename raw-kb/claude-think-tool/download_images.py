import asyncio
import httpx
import os

IMAGES = [
    ("tau_bench_airline", "https://www.anthropic.com/_next/image?url=https%3A%2F%2Fwww-cdn.anthropic.com%2Fimages%2F4zrzovbb%2Fwebsite%2Fff91e5c84be59ae71306bcc60adba9affed86484-2200x1300.jpg&w=3840&q=75"),
    ("tau_bench_retail", "https://www.anthropic.com/_next/image?url=https%3A%2F%2Fwww-cdn.anthropic.com%2Fimages%2F4zrzovbb%2Fwebsite%2F5819616b4cc109d30f1a7d47ec8a32a6b839637b-7638x4513.jpg&w=3840&q=75"),
]

async def download_image(client: httpx.AsyncClient, name: str, url: str, output_dir: str) -> bool:
    try:
        response = await client.get(url, timeout=30, follow_redirects=True)
        response.raise_for_status()
        
        content_type = response.headers.get("content-type", "")
        if "png" in content_type:
            ext = ".png"
        elif "jpeg" in content_type or "jpg" in content_type:
            ext = ".jpg"
        elif "svg" in content_type:
            ext = ".svg"
        else:
            ext = ".jpg"
        
        output_path = os.path.join(output_dir, f"{name}{ext}")
        with open(output_path, "wb") as f:
            f.write(response.content)
        print(f"Downloaded: {name}{ext}")
        return True
    except Exception as e:
        print(f"Failed to download {name}: {e}")
        return False

async def main():
    output_dir = os.path.dirname(os.path.abspath(__file__))
    os.makedirs(output_dir, exist_ok=True)
    
    async with httpx.AsyncClient() as client:
        tasks = [download_image(client, name, url, output_dir) for name, url in IMAGES]
        results = await asyncio.gather(*tasks)
    
    success_count = sum(results)
    print(f"\nDownload complete: {success_count}/{len(IMAGES)} images downloaded")

if __name__ == "__main__":
    asyncio.run(main())