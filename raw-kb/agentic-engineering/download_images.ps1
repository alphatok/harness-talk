$images = @(
    @{ url = "https://images.israynotarray.com/blog/ai/vide-agentic-engineering/ChatGPT%20Image%202026%E5%B9%B45%E6%9C%8817%E6%97%A5%20%E4%B8%8B%E5%8D%8802_43_12.png"; file = "cover.png" }
    @{ url = "https://israynotarray.com/images/favicon.png"; file = "favicon.png" }
)

$outDir = "d:\github\harness-talk\RAW-KB\agentic-engineering\images"
foreach ($img in $images) {
    $outFile = Join-Path $outDir $img.file
    if (-not (Test-Path $outFile)) {
        try {
            Write-Host "Downloading $($img.file)..."
            Invoke-WebRequest -Uri $img.url -OutFile $outFile -ErrorAction Stop
            Write-Host "  OK"
        } catch {
            Write-Host "  FAILED: $_"
        }
    } else {
        Write-Host "$($img.file) already exists"
    }
}
Write-Host "Done!"