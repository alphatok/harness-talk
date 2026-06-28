import asyncio
import httpx
import os

IMAGES = [
    ("diagram_01", "https://www.anthropic.com/_next/image?url=https%3A%2F%2Fwww-cdn.anthropic.com%2Fimages%2F4zrzovbb%2Fwebsite%2F903b624ada206b10753a24c6a1367e74a869165d-1080x1080.png&w=3840&q=75"),
    ("diagram_02", "https://www.anthropic.com/_next/image?url=https%3A%2F%2Fwww-cdn.anthropic.com%2Fimages%2F4zrzovbb%2Fwebsite%2F73e900af5b9d6ed8c64db0a8e74d4465963556b7-1640x1596.png&w=3840&q=75"),
    ("diagram_03", "https://www.anthropic.com/_next/image?url=https%3A%2F%2Fwww-cdn.anthropic.com%2Fimages%2F4zrzovbb%2Fwebsite%2Fcf0719d7832b1f577b7393c84a7c53eecc725ca4-760x200.png&w=1920&q=75"),
    ("diagram_04", "https://www.anthropic.com/_next/image?url=https%3A%2F%2Fwww-cdn.anthropic.com%2Fimages%2F4zrzovbb%2Fwebsite%2F4f67b1c10566552aec514a716ea43544ab330e0b-668x243.png&w=1920&q=75"),
]

async def download_image(client: httpx.AsyncClient, name: str, url: str, output_dir: str) -> bool:
    try:
        response = await client.get(url, timeout=30, follow_redirects=True)
        response.raise_for_status()
        
        # Determine extension from content-type
        content_type = response.headers.get("content-type", "")
        if "png" in content_type:
            ext = ".png"
        elif "svg" in content_type:
            ext = ".svg"
        elif "jpeg" in content_type or "jpg" in content_type:
            ext = ".jpg"
        else:
            ext = ".png"
        
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