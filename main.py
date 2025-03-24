from flet import *
import os
import pyperclip
import subprocess

def main(page:Page):
    # WindowSetting
    page.title = "NeCd"
    page.padding = 20
    page.window.min_width = 800
    page.window.width = 1000
    page.window.min_height = 700
    page.window.height = 800
    page.window.center()
    root_dir = os.path.dirname(os.path.abspath(__file__))
    page.window.icon = root_dir + "/icon.ico"

    # いろいろな変数
    outputpath = os.path.normpath(os.path.join(os.path.expanduser("~"),"yt-dlp")) + os.path.sep
    cookie_filepath = None
    download_process = None
    exts = [dropdown.Option(key="mp4",text="mp4"),dropdown.Option(key="mp3",text="mp3"),dropdown.Option(key="mkv",text="mkv"),dropdown.Option(key="opus",text="opus"),dropdown.Option(key="flac",text="flac"),]
    video_quality = [dropdown.Option(key="auto", text="自動"), dropdown.Option(key="2160", text="4K"), dropdown.Option(key="1440", text="2K"), dropdown.Option(key="1080", text="Full HD"), dropdown.Option(key="720", text="HD")]
    mp3_quality = [dropdown.Option(key="auto", text="自動"), dropdown.Option(key="320k", text="320kbps"), dropdown.Option(key="256k", text="256kbps"), dropdown.Option(key="192k", text="192kbps"), dropdown.Option(key="128k", text="128kbps")]

    def on_window_close(e):
        if download_process:
            try:
                download_process.terminate()
            except:
                pass
        page.window.destroy()
    
    page.on_close = on_window_close
    
    # print(outputpath)

    def change_cookiefrom(e):
        if cookiefrom.value == "file":
            cookies.visible = True
            cookies.update()
        else:
            cookies.visible = False
            cookies.update()
    
    def change_ext(e):
        if extdropdown.value == "mp4" or extdropdown.value == "mkv":
            qualitydropdown.options = video_quality
            qualitydropdown.value = video_quality[0].key
        elif extdropdown.value == "mp3":
            qualitydropdown.options = mp3_quality
            qualitydropdown.value = mp3_quality[0].key
        else:
            qualitydropdown.options = []
            qualitydropdown.value = ""
        qualitydropdown.update()
    
    def check_multiconnect(e):
        if multiconnect.value == "":
            pass
        else:
            # 数値かどうかチェック
            if multiconnect.value.isnumeric():
                # 0～16の範囲内かチェック
                if int(multiconnect.value) < 0 or int(multiconnect.value) > 16:
                    multiconnect.value = "16"
                    multiconnect.update()
            else:
                # 数値でない場合は16にリセット
                multiconnect.value = "16"
                multiconnect.update()
    
    def toggle_crop_thumbnail(e):
        is_cropthumbnail.disabled = not is_thumbnail.value
        if not is_thumbnail.value:
            is_cropthumbnail.value =False
        is_cropthumbnail.update()
    
    def paste_url(e):
        urlinput.value = pyperclip.paste()
        urlinput.update()

    def run_dlp(e):
        nonlocal download_process
        log.controls.clear()
        log.controls.append(Text("⏳ 開始しています...", color=Colors.BLUE, weight=FontWeight.BOLD))
        log.update()
        runbtn.disabled = True
        runbtn.text = "実行中"
        runbtn.icon = Icons.CACHED
        runbtn.update()
        progressbar.value = None
        progressbar.update()
        

        if urlinput.value == "":
            log.controls.append(Text("❌ URLを入力してください",weight=FontWeight.BOLD,color=Colors.RED))
            log.update()
            runbtn.disabled = False
            runbtn.text = "実行"
            runbtn.icon = Icons.PLAY_ARROW
            runbtn.update()
            progressbar.value = 0
            progressbar.update()
            return
        
        command = [
            "yt-dlp",
            "--newline",
            f"{urlinput.value}",
            "--embed-metadata","--add-metadata",
            "--default-search", "ytsearch",
            "--progress-template", "[DOWNLOADING]:%(progress._percent_str)s",
        ]

        if cookiefrom.value == "file":
            if cookie_filepath == None:
                log.controls.extend([
                    Text("❌ Cookieファイルが選択されていません",weight=FontWeight.BOLD,color=Colors.RED),
                    Text("Cookieを使用せずダウンロードします",color=Colors.RED)
                ])
                log.update()
            else:
                command.extend(["--cookies",cookie_filepath])
        elif cookiefrom.value == "firefox":
            command.extend(["--cookies-from-browser","firefox"])
        else:
            pass

        if extdropdown.value == "mp4":
            command.extend(["--merge-output-format","mp4"])
            if qualitydropdown.value != "auto":
                command.extend(["-f",f"bestvideo[height<={qualitydropdown.value}]+bestaudio[ext=m4a]/best[height<={qualitydropdown.value}]"])
            else:
                command.extend(["-f","bestvideo+bestaudio[ext=m4a]/best"])
        elif extdropdown.value == "mkv":
            command.extend(["--merge-output-format","mkv"])
            if qualitydropdown.value != "auto":
                command.extend(["-f",f"bestvideo[height<={qualitydropdown.value}]+bestaudio[ext=m4a]/best[height<={qualitydropdown.value}]"])
            else:
                command.extend(["-f","bestvideo+bestaudio[ext=m4a]/best"])
        elif extdropdown.value == "mp3":
            command.extend(["-f","bestaudio","-x","--audio-format","mp3"])
            if qualitydropdown.value != "auto":
                command.extend(["--audio-quality",qualitydropdown.value])
            else:
                command.extend(["--audio-quality","0"])
        else:
            command.extend(["-f","bestaudio","-x","--audio-format",extdropdown.value,"--audio-quality","0"])

        if multiconnect.value != "" and multiconnect.value != "0":
            command.extend(["-N", str(multiconnect.value)])

        if is_playlist.value:
            command.extend(["-o",outputpath + "%(playlist_title)s/%(playlist_index)03d_%(title)s.%(ext)s"])
        else:
            command.extend(["-o",outputpath + "%(title)s.%(ext)s"])
        
        if is_thumbnail.value:
            command.extend(["--embed-thumbnail","--convert-thumbnails","jpg"])
            if is_cropthumbnail.value:
                command.extend(["--ppa","ThumbnailsConvertor:-qmin 1 -q:v 1 -vf crop=\"'if(gt(ih,iw),iw,ih)':'if(gt(iw,ih),ih,iw)'\""])
        
        log.controls.extend([
            Text("📝 次のコマンドを実行します:",weight=FontWeight.BOLD),
            Text(" ".join(command),color=Colors.BLUE)
        ])
        log.update()
        p = subprocess.Popen(command,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,bufsize=1,universal_newlines=True)
        download_process = p

        # 標準出力の処理
        while True:
            output = p.stdout.readline()
            if output == "" and p.poll() is not None:
                break
            if output:
                if "[DOWNLOADING]" in output:
                    progress = output.split(":")[1].strip()
                    progressbar.value = float(progress.strip("%")) / 100
                    progressbar.update()
                else:
                    log.controls.append(Text(output.strip()))
                    log.scroll_to(offset=-1)
                    log.update()
                    progressbar.value = None
                    progressbar.update()

        # エラー出力を収集
        errors = p.stderr.read()
        
        p.wait()
        
        # エラーがあれば表示
        if errors:
            log.controls.append(Text("❌ 発生したエラー:", weight=FontWeight.BOLD, color=Colors.RED))
            for error_line in errors.splitlines():
                log.controls.append(Text(error_line, color=Colors.RED))
                log.scroll_to(offset=-1)
            log.update()
        
        if p.returncode == 0:
            log.controls.append(Text("✅ 正常に終了しました。",color=Colors.GREEN))
            log.scroll_to(offset=-1)
            log.update()
            progressbar.value = 1
            progressbar.update()
        else:
            log.controls.append(Text("❌ エラーが発生しました",color=Colors.RED))
            log.scroll_to(offset=-1)
            log.update()
            progressbar.value = 0
            progressbar.update()

        runbtn.disabled = False
        runbtn.text = "実行"
        runbtn.icon = Icons.PLAY_ARROW
        runbtn.update()
        download_process = None

    def select_outputpath(e:FilePickerResultEvent):
        nonlocal outputpath
        outputpath = os.path.normpath(e.path if e.path else outputpath) + os.path.sep
        # print(outputpath)
        outputpathfield.value = outputpath
        outputpathfield.update()
    
    def select_cookiefile(e: FilePickerResultEvent):
        nonlocal cookie_filepath
        if e.files:
            cookie_filepath = os.path.normpath(e.files[0].path)
        cookiefilepathfield.value = cookie_filepath if cookie_filepath else ""
        cookiefilepathfield.update()

    
    select_outputpath_dialog = FilePicker(on_result=select_outputpath)
    select_cookiefile_dialog = FilePicker(on_result=select_cookiefile)
    page.overlay.append(select_outputpath_dialog)
    page.overlay.append(select_cookiefile_dialog)
    
    urlinput = TextField(label="URL", prefix_icon=Icons.LINK, hint_text="https://youtube.com/watch?v=...", expand=True)
    pastebtn = IconButton(icon=Icons.PASTE, on_click=paste_url,tooltip="クリップボードから貼り付け")
    outputpathfield = TextField(value=outputpath, label="保存先", expand=True, read_only=True,prefix_icon=Icons.FOLDER)
    select_outputpath_btn = IconButton(icon=Icons.FOLDER_OPEN,tooltip="保存先を選択",on_click=lambda _:select_outputpath_dialog.get_directory_path(dialog_title="保存先を選択",initial_directory=os.path.expanduser("~")))
    cookiefrom = Dropdown(label="Cookie取得元",options=[dropdown.Option(key="none",text="なし"),dropdown.Option(key="file",text="ファイル"),dropdown.Option(key="firefox",text="Firefox")],value="none",on_change=change_cookiefrom)
    cookiefilepathfield = TextField(label="Cookieファイル(.txt)",expand=True,read_only=True,prefix_icon=Icons.COOKIE)
    select_cookiefile_btn = IconButton(icon=Icons.FILE_OPEN,on_click=lambda _:select_cookiefile_dialog.pick_files(dialog_title="Cookieファイルを選択",allow_multiple=False,allowed_extensions=["txt"]),tooltip="Cookieファイルを選択")
    cookies = Row([cookiefilepathfield,select_cookiefile_btn],visible=False)
    log = Column(controls=[Text("📃 ここにログが表示されます",weight=FontWeight.BOLD)], scroll=ScrollMode.AUTO, spacing=2, height=float("inf"), width=float("inf"), expand=True)
    extdropdown = Dropdown(label="拡張子",options=exts,value=exts[0].key,expand=True,on_change=change_ext,tooltip="保存するファイルの拡張子を選択します")
    qualitydropdown = Dropdown(label="品質",options=video_quality,value=video_quality[0].key,expand=True,tooltip="一部の拡張子の品質を選択します\n自動の場合は自動で選択された品質でダウンロードします")
    multiconnect = TextField(value=3, label="同時接続数(0~16)", tooltip=f"同時接続数を指定します\n0の場合は無効化します", on_change=check_multiconnect)
    is_playlist = Checkbox(label="プレイリストモード", tooltip="プレイリストをダウンロードする際に使うと便利です")
    is_thumbnail = Checkbox(label="サムネイルを埋め込む", tooltip="サムネイルを埋め込みます", on_change=toggle_crop_thumbnail)
    is_cropthumbnail = Checkbox(label="サムネイルをクロッピング", tooltip="サムネイルを1:1にクロッピングします\n有効にするには\"サムネイルを埋め込む\"を有効にしてください", disabled=True)
    runbtn = ElevatedButton(text="実行", icon=Icons.PLAY_ARROW, on_click=run_dlp, width=float("inf"))
    progressbar = ProgressBar(value=0,border_radius=border_radius.all(8))

    # 左パネル（コントロール類をまとめる）
    left_panel = Column(
        controls=[
            Row([Text(page.title, size=24, weight=FontWeight.BOLD),Text("Dev",color=Colors.BLACK45,size=12)]),
            Row([urlinput, pastebtn]),
            Row([outputpathfield, select_outputpath_btn]),
            cookiefrom,
            cookies,
            Row([extdropdown, qualitydropdown]),
            multiconnect,
            is_playlist,
            is_thumbnail,
            is_cropthumbnail,
            progressbar,
            runbtn
        ],
        spacing=18,
        width=400,
        scroll=ScrollMode.AUTO,
        alignment=MainAxisAlignment.START,
        height=float("inf"),
    )

    # 右パネル（ログを表示するエリア）
    right_panel = Container(
        content=log,
        border=border.all(1),
        border_radius=border_radius.all(8),
        padding=8,
        expand=True,
        height=float("inf")
    )

    # 全体レイアウトを行としてページに追加
    page.add(
        Row(
            [
                left_panel,
                right_panel
            ],
            spacing=20,
            expand=True
        )
    )

app(target=main)