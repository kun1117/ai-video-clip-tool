# generate_compilation.ps1
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptDir
$ffmpeg = Get-Command ffmpeg -ErrorAction SilentlyContinue
if (-not $ffmpeg) {
    Write-Host "[ERROR] ffmpeg not found!" -ForegroundColor Red
    exit 1
}
$clips = Get-ChildItem -Path $scriptDir -Filter 'leg_clip_*.mp4' | Sort-Object Name
if ($clips.Count -eq 0) {
    Write-Host "[ERROR] No leg_clip_*.mp4 files found." -ForegroundColor Red
    exit 1
}
$folderName = Split-Path $scriptDir -Leaf
$outputFile = "合集_${folderName}.mp4"
$outputPath = Join-Path $scriptDir $outputFile
Write-Host "Merging $($clips.Count) clips into $outputFile..."
$concatFile = Join-Path $scriptDir 'concat_list.txt'
$clips | ForEach-Object { "file '$($_.Name)'" } | Set-Content $concatFile -Encoding ASCII
& ffmpeg -y -f concat -safe 0 -i $concatFile -c copy $outputPath
if ($LASTEXITCODE -ne 0) {
    & ffmpeg -y -f concat -safe 0 -i $concatFile -c:v libx264 -crf 23 -c:a aac -b:a 128k -pix_fmt yuv420p $outputPath
}
Remove-Item $concatFile -Force -ErrorAction SilentlyContinue
Write-Host "[OK] $outputFile generated"
