# SlidesLive PPT 爬取方法论

## 适用场景

从 SlidesLive 平台（如 ICML、NeurIPS 等学术会议录像）爬取演示文稿幻灯片。

## 技术方案

### 1. 页面分析

SlidesLive 使用 `.slp__slidesPlayer` 播放器，通过 `SHIFT + ArrowRight` 键盘事件翻页。

### 2. 核心脚本

#### 获取所有幻灯片图片 URL

```javascript
async () => {
  const player = document.querySelector('.slp__slidesPlayer');
  if (!player) return 'Player not found';
  
  player.focus();
  await new Promise(r => setTimeout(r, 3000));
  
  // 获取当前幻灯片编号
  const getSlideNumber = () => {
    const slideText = document.body.innerText;
    const match = slideText.match(/Slide\s+(\d+)\s*\/\s*\d+/);
    return match ? parseInt(match[1]) : null;
  };
  
  // 获取当前图片URL
  const getCurrentImg = () => {
    const imgs = document.querySelectorAll('img');
    for (const img of imgs) {
      if (img.src && img.src.includes('slideslive-slides') && img.src.includes('original')) {
        return img.src;
      }
    }
    return null;
  };
  
  const slides = [];
  const totalSlides = 56; // 根据页面显示的总数调整
  
  for (let i = 1; i <= totalSlides; i++) {
    const slideNum = getSlideNumber();
    const url = getCurrentImg();
    slides.push({ slideNum, url });
    
    if (i < totalSlides) {
      const event = new KeyboardEvent('keydown', { 
        key: 'ArrowRight', 
        shiftKey: true,
        bubbles: true,
        cancelable: true,
        view: window
      });
      player.dispatchEvent(event);
      await new Promise(r => setTimeout(r, 800)); // 延迟确保图片加载
    }
  }
  
  return slides;
}
```

### 3. 执行流程

1. **打开 Chrome DevTools MCP**
2. **导航到 SlidesLive 页面**
   ```
   url: https://slideslive.com/{presentation_id}
   ```
3. **执行上述脚本**，获取所有幻灯片 URL 和对应的幻灯片编号
4. **提取 URL hash**：URL 格式为 `https://slideslive-slides.b-cdn.net/{id}/slides/original/{hash}.png?class=432`
5. **批量下载图片**

### 4. Python 下载脚本

```python
import asyncio
import httpx
import os

SLIDES_MAPPING = {
    "slide_01": "hash1",
    "slide_02": "hash2",
    # ... 根据抓取结果填充
}

async def download_slide(client: httpx.AsyncClient, name: str, hash: str, output_dir: str) -> bool:
    url = f"https://slideslive-slides.b-cdn.net/{presentation_id}/slides/original/{hash}.png?class=432"
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
        tasks = [download_slide(client, name, hash, output_dir) for name, hash in SLIDES_MAPPING.items()]
        await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(main())
```

### 5. 生成 Markdown 文档

```markdown
# {Presentation Title}

**Speaker**: {Name}
**Conference**: {Conference Name}
**Presentation ID**: {ID}

---

## Slide 1

![Slide 1](slide_01.png)

---

## Slide 2

> **Note**: This slide is a video segment without static image.

---

...
```

## 注意事项

### 视频片段

某些幻灯片编号对应的可能是视频片段而非静态图片（URL 为 `null`）。这些需要：
- 在 MD 文档中标注为视频片段
- 通过观看录像获取内容

### 正确顺序

务必通过 `getSlideNumber()` 函数获取当前幻灯片的实际编号，而非简单按遍历顺序命名，因为播放器可能会跳过某些页。

### 延迟设置

- 翻页后延迟：800ms - 1000ms（确保图片加载完成）
- 初始等待：2000ms - 3000ms（确保播放器初始化完成）

### URL 提取

图片 URL 格式：
```
https://slideslive-slides.b-cdn.net/{presentation_id}/slides/original/{hash}.png?class=432
```

关键参数：
- `presentation_id`: SlidesLive 演示 ID（如 39043876）
- `hash`: 图片唯一标识（8-16字符的随机字符串）
- `class`: 图片质量参数（432 表示原始质量）

## 工具依赖

- Chrome DevTools MCP（用于页面交互和脚本执行）
- Python 3.x + httpx（用于异步下载）

## 示例项目

参见 `raw-kb/icml-2025-shopify-sidekick/` 目录：
- `slides.md` - 幻灯片文档
- `slide_*.png` - 幻灯片图片（55张）
- `fix_slides.py` - 下载脚本