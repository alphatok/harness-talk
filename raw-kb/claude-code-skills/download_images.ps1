$images = @(
    @{ url = "https://cdn.prod.website-files.com/68a44d4040f98a4adf2207b6/6a0112e18cdd7f0b92d19e40_Hand-BuildingBricks.svg"; file = "Hand-BuildingBricks.svg" }
    @{ url = "https://cdn.prod.website-files.com/68a44d4040f98a4adf2207b6/6a1f3a763cec27e2f026439c_b7942952.png"; file = "skills-categories-chart.png" }
    @{ url = "https://cdn.prod.website-files.com/68a44d4040f98a4adf2207b6/6a1f3a763cec27e2f02643a2_6f109d87.png"; file = "skill-content-01.png" }
    @{ url = "https://cdn.prod.website-files.com/68a44d4040f98a4adf2207b6/6a1f3a763cec27e2f026439f_0e0f23c0.png"; file = "skill-content-02.png" }
    @{ url = "https://cdn.prod.website-files.com/68a44d4040f98a4adf2207b6/6a1f3a763cec27e2f02643ae_3c108f2c.png"; file = "skill-content-03.png" }
    @{ url = "https://cdn.prod.website-files.com/68a44d4040f98a4adf2207b6/6a1f3a763cec27e2f02643a8_d5e89124.png"; file = "skill-content-04.png" }
    @{ url = "https://cdn.prod.website-files.com/68a44d4040f98a4adf2207b6/6a1f3a763cec27e2f0264399_a60f7943.png"; file = "skill-content-05.png" }
    @{ url = "https://cdn.prod.website-files.com/68a44d4040f98a4adf2207b6/6a1f3a763cec27e2f02643b1_9159a9b1.png"; file = "skill-content-06.png" }
    @{ url = "https://cdn.prod.website-files.com/68a44d4040f98a4adf2207b6/6a1f3a763cec27e2f02643ab_00319576.png"; file = "skill-content-07.png" }
    @{ url = "https://cdn.prod.website-files.com/68a44d4040f98a4adf2207b6/6a1f3a763cec27e2f02643a5_32329bf3.png"; file = "skill-content-08.png" }
    @{ url = "https://cdn.prod.website-files.com/68a44d4040f98a4adf2207b6/6903d225588ad176f7c4aafd_abc884c723daea810d2e986455358281a2f94102-1000x1000.svg"; file = "icon-checklist.svg" }
    @{ url = "https://cdn.prod.website-files.com/68a44d4040f98a4adf2207b6/692f7912d5b05a5c7ed8ae86_Object-CodeChatCode.svg"; file = "icon-codechat.svg" }
    @{ url = "https://cdn.prod.website-files.com/68a44d4040f98a4adf2207b6/6903d2308749b4e883cc44b7_e029027e0b3beeb5b629bd4a26143597e7775b38-1000x1000.svg"; file = "icon-gear.svg" }
    @{ url = "https://cdn.prod.website-files.com/68a44d4040f98a4adf2207b6/6903d2222403b092e0358b0e_cd4fd51deacd067d4e30aee4f4b149f6cba1b97b-1000x1000.svg"; file = "icon-data.svg" }
)

$outDir = "d:\github\harness-talk\RAW-KB\claude-code-skills\images"
mkdir $outDir -Force | Out-Null

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
        Write-Host "$($img.file) already exists, skipping"
    }
}
Write-Host "Done!"