$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName PresentationFramework
$target = Join-Path $env:APPDATA 'Blackmagic Design\DaVinci Resolve\Support\Fusion\Scripts\Edit'
$resources = Join-Path $target 'TitanTitlesStudio'
$payload = Join-Path $PSScriptRoot 'Arquivos'
[xml]$markup = @'
<Window xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation" xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml" Title="Titan Titles Studio" Width="600" Height="620" ResizeMode="NoResize" WindowStartupLocation="CenterScreen" Background="#0B0F17" Foreground="#E2E8F0" FontFamily="Segoe UI">
 <Grid Margin="32">
  <Grid.RowDefinitions><RowDefinition Height="80"/><RowDefinition Height="28"/><RowDefinition Height="*"/><RowDefinition Height="56"/><RowDefinition Height="28"/></Grid.RowDefinitions>
  <Image x:Name="Brand" HorizontalAlignment="Left" Width="225" Stretch="Uniform"/>
  <TextBlock Grid.Row="1" Text="TITÂNIO • AZUL ELÉTRICO • @rangelmaker_" Foreground="#38BDF8" FontSize="11"/>
  <StackPanel Grid.Row="2" Margin="0,18,0,0">
   <TextBlock Text="Seu próximo título começa aqui." FontSize="24" FontWeight="SemiBold" Margin="0,0,0,14"/>
   <TextBlock Text="Layouts, tipografia e movimento para DaVinci Resolve." Foreground="#94A3B8" TextWrapping="Wrap" Margin="0,0,0,18"/>
   <Border Background="#111827" CornerRadius="12" Padding="18"><StackPanel>
    <TextBlock Text="Instalação no seu usuário • sem administrador" FontSize="14"/>
    <TextBlock Text="Atualizações pelo GitHub com backup automático." Foreground="#94A3B8" Margin="0,8,0,0" TextWrapping="Wrap"/>
   </StackPanel></Border>
   <CheckBox x:Name="Clean" Content="Remover a versão Titan anterior antes de instalar" Margin="0,20,0,0" Foreground="#E2E8F0"/>
   <TextBlock x:Name="Status" Text="Feche o plugin antes de instalar ou remover." Foreground="#38BDF8" Margin="0,14,0,0" TextWrapping="Wrap"/>
  </StackPanel>
  <Grid Grid.Row="3"><Grid.ColumnDefinitions><ColumnDefinition Width="*"/><ColumnDefinition Width="16"/><ColumnDefinition Width="*"/></Grid.ColumnDefinitions>
   <Button x:Name="Remove" Content="Remover Titan" Height="40" Background="#1E293B" Foreground="#E2E8F0" BorderThickness="0"/>
   <Button x:Name="Install" Grid.Column="2" Content="Instalar / atualizar" Height="40" Background="#38BDF8" Foreground="#0B0F17" FontWeight="Bold" BorderThickness="0"/>
  </Grid>
  <TextBlock Grid.Row="4" Text="Titan Titles Studio • v3.2.0" Foreground="#64748B" VerticalAlignment="Bottom" FontSize="11"/>
 </Grid>
</Window>
'@
$window = [Windows.Markup.XamlReader]::Load((New-Object Xml.XmlNodeReader $markup))
$brand = Join-Path $payload 'icons\titan_word.png'
if (Test-Path -LiteralPath $brand) { $window.FindName('Brand').Source = $brand }
$status = $window.FindName('Status')
function Assert-TitanPath([string]$path) {
    $resolved = [IO.Path]::GetFullPath($path)
    $base = [IO.Path]::GetFullPath($target).TrimEnd('\') + '\'
    if (-not $resolved.StartsWith($base, [StringComparison]::OrdinalIgnoreCase)) { throw 'Destino inesperado.' }
    $check = $resolved
    while ($check -and $check.Length -ge [IO.Path]::GetFullPath($target).Length) {
        if ((Test-Path -LiteralPath $check) -and ((Get-Item -LiteralPath $check -Force).Attributes -band [IO.FileAttributes]::ReparsePoint)) { throw 'Pasta redirecionada; instalação interrompida.' }
        $check = Split-Path -Parent $check
    }
}
function Backup-Titan {
    $parent = Join-Path $target 'TitanTitlesStudio-backups'
    Assert-TitanPath $parent
    $backup = Join-Path $parent ([Guid]::NewGuid().ToString())
    New-Item -ItemType Directory -Path $backup -Force | Out-Null
    $script = Join-Path $target 'Titan Titles Studio.py'
    Assert-TitanPath $script
    Assert-TitanPath $resources
    if (Test-Path -LiteralPath $script) { Copy-Item -LiteralPath $script -Destination $backup }
    if (Test-Path -LiteralPath $resources) { Copy-Item -LiteralPath $resources -Destination $backup -Recurse }
    return $backup
}
function Remove-Titan {
    $script = Join-Path $target 'Titan Titles Studio.py'
    Assert-TitanPath $script
    Assert-TitanPath $resources
    if (Test-Path -LiteralPath $script) { Remove-Item -LiteralPath $script }
    if (Test-Path -LiteralPath $resources) { Remove-Item -LiteralPath $resources -Recurse }
}
$window.FindName('Install').Add_Click({
    $backup = $null
    try {
        foreach ($part in @('Titan Titles Studio.py','titan_update.py','icons')) {
            if (-not (Test-Path -LiteralPath (Join-Path $payload $part))) { throw 'Pacote incompleto. Extraia o ZIP inteiro antes de instalar.' }
        }
        $backup = Backup-Titan
        if ($window.FindName('Clean').IsChecked) { Remove-Titan }
        Assert-TitanPath $resources
        New-Item -ItemType Directory -Path $resources -Force | Out-Null
        Copy-Item -LiteralPath (Join-Path $payload 'icons') -Destination $resources -Recurse -Force
        Copy-Item -LiteralPath (Join-Path $payload 'titan_update.py') -Destination $resources -Force
        Copy-Item -LiteralPath (Join-Path $payload 'Titan Titles Studio.py') -Destination $target -Force
        $status.Text = 'Instalado! Abra Workspace > Scripts > Edit > Titan Titles Studio.'
    } catch {
        if ($backup) {
            try {
                Remove-Titan
                if (Test-Path -LiteralPath (Join-Path $backup 'TitanTitlesStudio')) { Copy-Item -LiteralPath (Join-Path $backup 'TitanTitlesStudio') -Destination $target -Recurse -Force }
                if (Test-Path -LiteralPath (Join-Path $backup 'Titan Titles Studio.py')) { Copy-Item -LiteralPath (Join-Path $backup 'Titan Titles Studio.py') -Destination $target -Force }
            } catch { $status.Text = "Falha ao restaurar. Backup: $backup"; return }
        }
        $status.Text = 'Falha na instalação: ' + $_.Exception.Message
    }
})
$window.FindName('Remove').Add_Click({
    if ([Windows.MessageBox]::Show('Remover apenas o Titan Titles Studio? Outros plugins serão preservados. Uma cópia de segurança será guardada.', 'Titan Titles Studio', 'YesNo', 'Question') -ne 'Yes') { return }
    try { $null = Backup-Titan; Remove-Titan; $status.Text = 'Titan removido. Backup preservado.' }
    catch { $status.Text = 'Não foi possível remover: ' + $_.Exception.Message }
})
$null = $window.ShowDialog()
