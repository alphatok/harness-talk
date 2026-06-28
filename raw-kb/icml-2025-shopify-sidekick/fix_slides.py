import asyncio
import httpx
import os

# 正确的幻灯片映射
SLIDES_MAPPING = {
    "slide_01": "QsRtQGoijDLfgWfR",
    "slide_03": "FSExkSyl994jip0I",
    "slide_04": "K1TDnaEn7mtFH2Mo",  # 新增！之前缺失
    "slide_05": "Ce2TPv2Tv5fC7Jrm",
    "slide_06": "xtidWH7WCgnZLrfx",
    "slide_07": "TS9ISLsCJKa2yfBD",
    "slide_08": "Q2eKFIwBvm8KZ156",
    "slide_09": "u0TDqqgmBTIjcxJs",
    "slide_10": "2hmV1DPscDQlIhmC",
    "slide_11": "tEEA8ztpJoKVYxEt",
    "slide_12": "8DbCMy2so8ayCaje",
    "slide_13": "mCUazuV38QzTqDRD",
    "slide_14": "Z6HAnakhGyq4xr3Q",
    "slide_15": "ogPXltjzoJ7l1owl",
    "slide_16": "eBRpsbThTZCL8jQo",
    "slide_17": "BqcpxKza84ZBUhw4",
    "slide_18": "5XVldW6D4hpEUqOG",
    "slide_19": "wIXUKIwwXxrQ8SR7",
    "slide_20": "r86N4LgqKYCqHavZ",
    "slide_21": "5a9VDrZPTF8lqElX",
    "slide_22": "fLV5Ol9aBCpqVylr",
    "slide_23": "EP7URr0C7qb53FmM",
    "slide_24": "AZwno2LUVUL7mwnz",
    "slide_25": "zDaytuYcM03GOZy2",
    "slide_26": "vhcB0nQWlVIGfKNf",
    "slide_27": "jQr69ivGoE0YSBge",
    "slide_28": "qvmrSTFRCvxrtO83",
    "slide_29": "HQsD8BliPQRQh9s5",
    "slide_30": "YvwXXsc90ydmNwn7",
    "slide_31": "KueIwrI58K14Oc1l",
    "slide_32": "IC16K93z66vmVEai",
    "slide_33": "jqpOiKfHwFyWcUS5",
    "slide_34": "Wz1DY1e1aHRhv1mt",
    "slide_35": "tDBYERANzGFaCfM9",
    "slide_36": "TJTMcVTcJnyufLh0",
    "slide_37": "7jbJM8q6DnLSxymm",
    "slide_38": "MJc1rxwU70uwzvO7",
    "slide_39": "vQ1Zx16LSksM0S66",
    "slide_40": "BxeRWGvrNBWxoESG",
    "slide_41": "YIkzRjSKmYTguHq5",
    "slide_42": "lPqqkNa0uQBBUAOq",
    "slide_43": "sAS8Fmv5i88Jt14g",
    "slide_44": "yCsfQvCjXNEPYpSS",
    "slide_45": "YFr4TBrsaDfwuK0J",
    "slide_46": "7LCqq7RJBcNYLawE",
    "slide_47": "bKn2dj4YDQ1JUlAo",
    "slide_48": "inX3rKsCFz6ZFvGP",
    "slide_49": "wcGSu8c1m3oKYXpj",
    "slide_50": "fhDdGPMKl9oCFHOJ",
    "slide_51": "RZXMsufUkLKA3uK4",
    "slide_52": "2Z2FE85QZyqxQKco",
    "slide_53": "1R1WxIKdIJc2ChoK",
    "slide_54": "ErgQMveI6MaVEqHW",
    "slide_55": "k2c35yZlaFPfHRLb",
    "slide_56": "zpHTETEVzYltjPau",  # 新增！之前缺失
}

async def download_slide(client: httpx.AsyncClient, name: str, hash: str, output_dir: str) -> bool:
    url = f"https://slideslive-slides.b-cdn.net/39043876/slides/original/{hash}.png?class=432"
    output_path = os.path.join(output_dir, f"{name}.png")
    
    # 如果文件已存在，跳过
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
        print(f"Failed to download {name}: {e}")
        return False

async def main():
    output_dir = os.path.dirname(os.path.abspath(__file__))
    
    async with httpx.AsyncClient() as client:
        tasks = [download_slide(client, name, hash, output_dir) for name, hash in SLIDES_MAPPING.items()]
        results = await asyncio.gather(*tasks)
    
    success_count = sum(results)
    print(f"\nComplete: {success_count}/{len(SLIDES_MAPPING)} slides")

if __name__ == "__main__":
    asyncio.run(main())