// ocr.swift — macOS Vision OCR（中文 + 英文）
// 用途：客户会议相关截图/文档图片的文字提取（UGC 活动页、企业微信对话、邮件截图等）
// 平台：仅 macOS（依赖 Vision + AppKit）。非 macOS 或无 swift 时，回退为请用户描述图片内容。
//
// 用法：
//   swift ocr.swift <图片路径> [更多图片路径...]
// 输出：每个文件一段 "===== FILE: <路径> =====" 后接按视觉顺序排列的识别文本行。
//
// 说明：识别语言 zh-Hans + en-US，开启语句修正；识别结果按行输出，保留原始阅读顺序。

import Foundation
import Vision
import AppKit

let args = CommandLine.arguments
guard args.count > 1 else {
    print("usage: swift ocr.swift <image> [image2 ...]")
    exit(1)
}

func ocr(_ path: String) {
    print("===== FILE: \(path) =====")
    guard let img = NSImage(contentsOfFile: path),
          let cg = img.cgImage(forProposedRect: nil, context: nil, hints: nil) else {
        print("[OCR 失败] 无法读取图片: \(path)")
        return
    }
    let request = VNRecognizeTextRequest { req, _ in
        guard let obs = req.results as? [VNRecognizedTextObservation] else { return }
        for o in obs {
            if let t = o.topCandidates(1).first {
                print(t.string)
            }
        }
    }
    request.recognitionLevel = .accurate
    request.recognitionLanguages = ["zh-Hans", "en-US"]
    request.usesLanguageCorrection = true
    let handler = VNImageRequestHandler(cgImage: cg, options: [:])
    do {
        try handler.perform([request])
    } catch {
        print("[OCR 失败] \(path): \(error.localizedDescription)")
    }
}

for path in args.dropFirst() {
    ocr(path)
}
