# Script to clean up temporary files while preserving important ones

# Files to keep (add more if needed)
$filesToKeep = @(
    "init_db.py",
    "setup.py",
    "requirements.txt",
    "README.md"
)

# Directories to keep (add more if needed)
$dirsToKeep = @(
    "tenants_manager",
    "tests",
    "data"
)

Write-Host "=== Cleaning up temporary files ==="

# Remove temporary Python files
Get-ChildItem -Path . -Filter *.py | ForEach-Object {
    if ($filesToKeep -notcontains $_.Name) {
        Write-Host "Removing: $($_.Name)"
        Remove-Item -Path $_.FullName -Force
    }
}

# Remove batch files
Get-ChildItem -Path . -Filter *.bat | ForEach-Object {
    Write-Host "Removing: $($_.Name)"
    Remove-Item -Path $_.FullName -Force
}

# Remove temporary text files
Get-ChildItem -Path . -Filter *.txt | Where-Object { $_.Name -ne "requirements.txt" } | ForEach-Object {
    Write-Host "Removing: $($_.Name)"
    Remove-Item -Path $_.FullName -Force
}

Write-Host "`nCleanup complete!"
Write-Host "Remaining Python files:"
Get-ChildItem -Path . -Filter *.py | Select-Object -ExpandProperty Name
