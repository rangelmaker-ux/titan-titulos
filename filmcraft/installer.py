"""Per-user Windows installer; never writes inside FilmCraft or Resolve."""
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import tkinter as tk
from tkinter import ttk,messagebox
from titan_filmcraft import ROOT,DATA,VERSION,filmcraft_path

TARGET=Path(os.environ.get('LOCALAPPDATA',str(Path.home())))/'Programs/TitanFilmCraft'
EXE=TARGET/'TitanFilmCraft.exe'
LINK='Titan Titles Studio - FilmCraft.lnk'

def shortcut(create):
    # Paths cross the shell as environment values, never as interpolated code.
    env=os.environ.copy();env['TITAN_FC_EXE']=str(EXE);env['TITAN_FC_LINK']=LINK
    script=r'''
$ErrorActionPreference='Stop'
$desktop=[Environment]::GetFolderPath('Desktop')
$menu=[Environment]::GetFolderPath('Programs')
foreach ($directory in @($desktop,$menu)) {
    $linkPath=Join-Path $directory $env:TITAN_FC_LINK
    if ($env:TITAN_FC_CREATE -eq '1') {
        $ws=New-Object -ComObject WScript.Shell
        $link=$ws.CreateShortcut($linkPath)
        $link.TargetPath=$env:TITAN_FC_EXE
        $link.WorkingDirectory=Split-Path -Parent $env:TITAN_FC_EXE
        $link.Description='Titan Titles Studio para FilmCraft'
        $link.Save()
    } elseif (Test-Path -LiteralPath $linkPath) {
        Remove-Item -LiteralPath $linkPath
    }
}
'''
    env['TITAN_FC_CREATE']='1' if create else '0'
    result=subprocess.run(['powershell','-NoProfile','-NonInteractive','-Command',script],env=env,
                          capture_output=True,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
    if result.returncode:raise RuntimeError(result.stderr.decode('utf-8','replace'))

def install(source=None):
    filmcraft_path()
    source=Path(source or sys.executable).resolve()
    if not source.is_file():raise ValueError('Instalador ausente.')
    TARGET.mkdir(parents=True,exist_ok=True)
    stage=TARGET/('TitanFilmCraft-'+str(os.getpid())+'.tmp')
    try:
        shutil.copy2(source,stage);os.replace(stage,EXE)
    except PermissionError:
        raise RuntimeError('Feche o Titan para FilmCraft antes de instalar a nova versão.')
    finally:stage.unlink(missing_ok=True)
    shortcut(True)

def uninstall():
    # Known executable and shortcuts only. Audio paths in existing projects stay valid.
    if EXE.is_file():
        try:EXE.unlink()
        except PermissionError:raise RuntimeError('Feche o Titan para FilmCraft antes de remover.')
    shortcut(False)

def main():
    root=tk.Tk();root.title('Instalar • Titan Titles Studio para FilmCraft');root.geometry('570x570');root.resizable(False,False);root.configure(bg='#10151e')
    style=ttk.Style(root);style.theme_use('clam')
    style.configure('TFrame',background='#10151e');style.configure('TLabel',background='#10151e',foreground='#edf4ff',font=('Segoe UI',11))
    style.configure('TButton',background='#009fff',foreground='white',padding=12,font=('Segoe UI',11,'bold'))
    style.map('TButton',background=[('active','#0078c4')])
    card=ttk.Frame(root,padding=30);card.pack(fill='both',expand=True)
    try:
        from PIL import Image,ImageTk
        image=Image.open(ROOT/'icons/titan_word.png');image.thumbnail((350,95));root.logo=ImageTk.PhotoImage(image)
        ttk.Label(card,image=root.logo).pack(anchor='w')
    except Exception:ttk.Label(card,text='TITAN TITLES STUDIO',font=('Segoe UI',22,'bold')).pack(anchor='w')
    ttk.Label(card,text='FILMCRAFT  •  WINDOWS  •  '+VERSION,foreground='#00b7ff').pack(anchor='w',pady=(12,20))
    ttk.Label(card,text='Legendas comuns, dinâmicas e mistas.\nSeis animações com sons nos destaques.\nTextos editáveis na timeline do FilmCraft.',wraplength=500).pack(anchor='w',pady=(0,16))
    ttk.Label(card,text='Instala para este usuário, sem precisar de Python.\nUma nova instalação substitui a versão anterior.',foreground='#9aaac0',wraplength=500).pack(anchor='w')
    status=tk.StringVar();ttk.Label(card,textvariable=status,wraplength=500).pack(anchor='w',pady=10)
    def action(remove=False):
        try:
            if remove:
                uninstall();status.set('Titan removido. Projetos e áudios gerados foram preservados.');return
            install();status.set('Instalado! Use o atalho Titan Titles Studio - FilmCraft.')
            if messagebox.askyesno('Titan','Abrir o Titan agora?',parent=root):subprocess.Popen([str(EXE)])
        except Exception as error:messagebox.showerror('Titan',str(error),parent=root)
    ttk.Button(card,text='INSTALAR / ATUALIZAR',command=action).pack(fill='x',pady=5)
    if EXE.is_file():ttk.Button(card,text='Remover versão instalada',command=lambda:action(True)).pack(fill='x',pady=5)
    root.mainloop()
