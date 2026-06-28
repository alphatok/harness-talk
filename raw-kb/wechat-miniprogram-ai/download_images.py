import asyncio
import httpx
import os

IMAGES = [
    ("img-1", "https://res8.wxqcloud.qq.com.cn/wxdoc/9943309d-a354-4ca0-a8e5-9d21d8f1868b.png"),
    ("img-2", "https://res8.wxqcloud.qq.com.cn/wxdoc/32b1abaf-6614-420b-baef-883a2e9c561b.png"),
    ("img-3", "https://res8.wxqcloud.qq.com.cn/wxdoc/98bddeb9-c8ca-4fce-9ead-3189966edeaf.png"),
    ("img-4", "https://res8.wxqcloud.qq.com.cn/wxdoc/34a8fd99-25a0-4ce6-91ad-2ec4b4fa4784.png"),
    ("img-5", "https://res8.wxqcloud.qq.com.cn/wxdoc/ccb8e6cf-534c-47cf-a17f-66986cec5794.png"),
    ("img-6", "https://res8.wxqcloud.qq.com.cn/wxdoc/f0cb04bc-228b-403d-813e-a2404f944477.png"),
    ("img-7", "https://res8.wxqcloud.qq.com.cn/wxdoc/9cbe51e8-127d-4b8d-a728-03895b00f755.png"),
    ("img-8", "https://res8.wxqcloud.qq.com.cn/wxdoc/c735171b-287a-4aa7-941f-edecbfebfc71.png"),
    ("img-9", "https://res8.wxqcloud.qq.com.cn/wxdoc/d2138391-efee-40a7-b513-1e265c841bfc.png"),
    ("img-10", "https://res8.wxqcloud.qq.com.cn/wxdoc/c772365d-0b2a-46e9-9efc-73a1efc9d772.png"),
    ("img-11", "https://res8.wxqcloud.qq.com.cn/wxdoc/56617deb-b17d-4cf1-bccd-71d2c41ccc76.svg"),
]

async def download_image(client: httpx.AsyncClient, name: str, url: str, output_dir: str) -> bool:
    try:
        response = await client.get(url, timeout=30, follow_redirects=True)
        response.raise_for_status()
        
        content_type = response.headers.get("content-type", "")
        if "png" in content_type or url.endswith(".png"):
            ext = ".png"
        elif "svg" in content_type or url.endswith(".svg"):
            ext = ".svg"
        elif "jpeg" in content_type or "jpg" in content_type or url.endswith(".jpg"):
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