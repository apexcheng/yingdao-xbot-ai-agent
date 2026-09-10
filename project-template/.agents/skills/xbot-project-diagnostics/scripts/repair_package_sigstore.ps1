param(
    [string]$ProjectRoot = ".",
    [string]$RuntimePath = "",
    [switch]$Write
)

$ErrorActionPreference = "Stop"

$projectRootPath = (Resolve-Path $ProjectRoot).Path
$packageJsonPath = Join-Path $projectRootPath "package.json"
if (-not (Test-Path $packageJsonPath)) {
    throw "目标目录缺少 package.json：$packageJsonPath"
}

if (-not $RuntimePath) {
    $shadowBotRoot = Join-Path $env:ProgramFiles "ShadowBot"
    $runtimeDirectory = Get-ChildItem $shadowBotRoot -Directory -Filter "shadowbot-*" |
        ForEach-Object {
            $versionText = $_.Name -replace '^shadowbot-', ''
            try { $version = [version]$versionText } catch { $version = [version]'0.0' }
            [pscustomobject]@{ Directory = $_; Version = $version }
        } |
        Where-Object { Test-Path (Join-Path $_.Directory.FullName "ShadowBot.Runtime.dll") } |
        Sort-Object Version -Descending |
        Select-Object -First 1

    if (-not $runtimeDirectory) {
        throw "未找到已安装的 ShadowBot.Runtime.dll"
    }
    $RuntimePath = Join-Path $runtimeDirectory.Directory.FullName "ShadowBot.Runtime.dll"
} else {
    $RuntimePath = (Resolve-Path $RuntimePath).Path
}

$dotnet = Get-Command dotnet -ErrorAction Stop

if ($Write) {
    $sigstorePath = Join-Path $projectRootPath "package.sigstore"
    if (Test-Path $sigstorePath) {
        $backupDir = Join-Path $projectRootPath ".dev\repair-backups"
        New-Item -ItemType Directory -Path $backupDir -Force | Out-Null
        $backupPath = Join-Path $backupDir ("package.sigstore.{0}.bak" -f (Get-Date -Format "yyyyMMdd-HHmmss"))
        Copy-Item $sigstorePath $backupPath
        Write-Host "backup=$backupPath"
    }
}

$tempDir = Join-Path $env:TEMP ("shadowbot-sigstore-{0}" -f ([guid]::NewGuid().ToString("N")))
New-Item -ItemType Directory -Path $tempDir | Out-Null

try {
    @'
<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <OutputType>Exe</OutputType>
    <TargetFramework>net8.0</TargetFramework>
    <ImplicitUsings>disable</ImplicitUsings>
    <Nullable>enable</Nullable>
  </PropertyGroup>
</Project>
'@ | Set-Content -Path (Join-Path $tempDir "SigstoreRepair.csproj") -Encoding UTF8

    @'
using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Reflection;
using System.Runtime.Loader;
using System.Text.Json;

class Program
{
    static void Main(string[] args)
    {
        var runtimePath = Path.GetFullPath(args[0]);
        var projectDir = Path.GetFullPath(args[1]);
        var runtimeDir = Path.GetDirectoryName(runtimePath)!;
        var shadowBotRoot = Directory.GetParent(runtimeDir)!.FullName;

        var probeDirectories = new List<string> { runtimeDir };
        foreach (var relativeRoot in new[]
        {
            Path.Combine("dotnet.win-x64", "shared", "Microsoft.WindowsDesktop.App"),
            Path.Combine("dotnet.win-x64", "shared", "Microsoft.NETCore.App")
        })
        {
            var root = Path.Combine(shadowBotRoot, relativeRoot);
            if (Directory.Exists(root))
                probeDirectories.AddRange(Directory.GetDirectories(root).OrderByDescending(path => path, StringComparer.OrdinalIgnoreCase));
        }
        probeDirectories.Add(Path.Combine(runtimeDir, "support_x64", "ProcessLauncher"));

        AssemblyLoadContext.Default.Resolving += (_, name) =>
        {
            foreach (var directory in probeDirectories)
            {
                var candidate = Path.Combine(directory, name.Name + ".dll");
                if (File.Exists(candidate))
                    return AssemblyLoadContext.Default.LoadFromAssemblyPath(candidate);
            }
            return null;
        };

        using var document = JsonDocument.Parse(File.ReadAllText(Path.Combine(projectDir, "package.json")));
        var rootElement = document.RootElement;
        var appId = rootElement.GetProperty("uuid").GetString()!;
        var appName = rootElement.GetProperty("name").GetString()!;

        var assembly = AssemblyLoadContext.Default.LoadFromAssemblyPath(runtimePath);
        var appInfoType = assembly.GetType("ShadowBot.Runtime.Packages.PackageAppInfo")!;
        var packageType = assembly.GetType("ShadowBot.Runtime.Packages.Package")!;
        var helperType = assembly.GetType("ShadowBot.Runtime.Packages.PackageHelper")!;

        var appInfo = Activator.CreateInstance(appInfoType)!;
        appInfoType.GetProperty("AppId")!.SetValue(appInfo, appId);
        appInfoType.GetProperty("Name")!.SetValue(appInfo, appName);

        var constructor = packageType.GetConstructor(new[] { typeof(string), appInfoType, typeof(bool?), typeof(string), typeof(bool) })!;
        var package = constructor.Invoke(new object?[]
        {
            Directory.GetParent(projectDir)!.FullName,
            appInfo,
            null,
            Path.GetFileName(projectDir),
            false
        });

        var test = helperType.GetMethod("TestPackageSigstore", BindingFlags.Public | BindingFlags.Static)!;
        var write = helperType.GetMethod("WritePackageSigstore", BindingFlags.Public | BindingFlags.Static)!;

        Console.WriteLine("before=" + test.Invoke(null, new[] { package }));
        if (args.Length >= 3 && args[2] == "write")
        {
            write.Invoke(null, new[] { package });
            Console.WriteLine("after=" + test.Invoke(null, new[] { package }));
        }
    }
}
'@ | Set-Content -Path (Join-Path $tempDir "Program.cs") -Encoding UTF8

    $mode = if ($Write) { "write" } else { "check" }
    & $dotnet.Source run --project (Join-Path $tempDir "SigstoreRepair.csproj") --configuration Release -- $RuntimePath $projectRootPath $mode
    if ($LASTEXITCODE -ne 0) {
        throw "Sigstore 校验 / 修复程序执行失败，exit_code=$LASTEXITCODE"
    }
} finally {
    Remove-Item $tempDir -Recurse -Force -ErrorAction SilentlyContinue
}
