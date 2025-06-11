# 必要なライブラリのインポート
from flet import *
import os
import pyperclip
import logging
import datetime
import subprocess
from queue import Queue
import json

# ログディレクトリの作成
os.makedirs('./logs', exist_ok=True)

# 設定ファイルのパス
SETTINGS_FILE = "settings.json"
VERSION = "1.1.2"

def load_settings():
    """
    設定ファイルから設定を読み込む
    Returns:
        dict: 設定データ
    """
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_settings(settings):
    """
    設定をファイルに保存
    Args:
        settings (dict): 保存する設定データ
    """
    with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
        json.dump(settings, f, ensure_ascii=False, indent=4)

def main(page: Page):
    """
    メインウィンドウの設定と初期化
    Args:
        page (Page): Fletのページオブジェクト
    """
    # ウィンドウの基本設定
    page.title = f"NeCd"
    page.padding = 12
    page.window.min_width = 800
    page.window.width = 1200
    page.window.min_height = 700
    page.window.height = 800
    page.window.center()
    root_dir = os.path.dirname(os.path.abspath(__file__))
    page.window.icon = root_dir + "/icon.ico"

    # 設定の読み込み
    settings = load_settings()
    
    # グローバル変数の初期化
    download_directory = settings.get('download_directory', os.path.normpath(os.path.join(os.path.expanduser("~"), "yt-dlp")) + os.path.sep)
    cookie_file_path = settings.get('cookie_file_path', None)
    download_process = None

    # ドロップダウンの選択肢設定
    file_format_options = [
        dropdown.Option(key="mp4", text="mp4"),
        dropdown.Option(key="mp3", text="mp3"),
        dropdown.Option(key="mkv", text="mkv"),
        dropdown.Option(key="opus", text="opus"),
        dropdown.Option(key="flac", text="flac"),
    ]
    video_quality_options = [
        dropdown.Option(key="auto", text="自動"),
        dropdown.Option(key="2160", text="4K"),
        dropdown.Option(key="1440", text="2K"),
        dropdown.Option(key="1080", text="Full HD"),
        dropdown.Option(key="720", text="HD")
    ]
    audio_quality_options = [
        dropdown.Option(key="auto", text="自動"),
        dropdown.Option(key="320k", text="320kbps"),
        dropdown.Option(key="256k", text="256kbps"),
        dropdown.Option(key="192k", text="192kbps"),
        dropdown.Option(key="128k", text="128kbps")
    ]

    def handle_window_close(e):
        """
        ウィンドウを閉じる際の処理
        実行中のダウンロードプロセスを終了し、ウィンドウを閉じる
        """
        if download_process:
            try:
                download_process.terminate()
            except:
                pass
        page.window.destroy()
    
    page.on_close = handle_window_close

    def handle_cookie_source_change(e):
        """
        Cookieの取得元を変更した際の処理
        Args:
            e: イベントオブジェクト
        """
        if cookie_source_dropdown.value == "file":
            cookie_file_row.visible = True
            cookie_file_row.update()
        else:
            cookie_file_row.visible = False
            cookie_file_row.update()
    
    def handle_format_change(e):
        """
        拡張子を変更した際の処理
        選択された拡張子に応じて品質設定とチャプター設定を更新
        Args:
            e: イベントオブジェクト
        """
        if format_dropdown.value == "mp4" or format_dropdown.value == "mkv":
            quality_dropdown.options = video_quality_options
            quality_dropdown.value = video_quality_options[0].key
            chapter_checkbox.disabled = False
        elif format_dropdown.value == "mp3":
            quality_dropdown.options = audio_quality_options
            quality_dropdown.value = audio_quality_options[0].key
            chapter_checkbox.disabled = True
            chapter_checkbox.value = False
        else:
            quality_dropdown.options = []
            quality_dropdown.value = ""
            chapter_checkbox.disabled = True
            chapter_checkbox.value = False
        quality_dropdown.update()
        chapter_checkbox.update()
    
    def validate_concurrent_connections(e):
        """
        同時接続数の入力値を検証
        0～16の範囲内の数値のみ許可
        Args:
            e: イベントオブジェクト
        """
        if concurrent_connections_input.value == "":
            pass
        else:
            if concurrent_connections_input.value.isnumeric():
                if int(concurrent_connections_input.value) < 0 or int(concurrent_connections_input.value) > 16:
                    concurrent_connections_input.value = "16"
                    concurrent_connections_input.update()
            else:
                concurrent_connections_input.value = "16"
                concurrent_connections_input.update()
    
    def handle_thumbnail_crop_toggle(e):
        """
        サムネイルクロッピングの有効/無効を切り替え
        サムネイル埋め込みが無効の場合はクロッピングも無効化
        Args:
            e: イベントオブジェクト
        """
        thumbnail_crop_checkbox.disabled = not thumbnail_checkbox.value
        if not thumbnail_checkbox.value:
            thumbnail_crop_checkbox.value = False
        thumbnail_crop_checkbox.update()
    
    def handle_url_paste(e):
        """
        クリップボードからURLを貼り付け
        Args:
            e: イベントオブジェクト
        """
        url_input.value = pyperclip.paste()
        url_input.update()

    def execute_download(e):
        """
        動画ダウンロードの実行
        ダウンロードを実行し、進捗状況を表示
        Args:
            e: イベントオブジェクト
        """
        nonlocal download_process
        
        # UIの初期状態設定
        log_output.controls.clear()
        log_output.controls.append(Text("⏳ 開始しています...", color=Colors.BLUE, weight=FontWeight.BOLD))
        log_output.update()
        download_button.disabled = True
        download_button.text = "実行中"
        download_button.icon = Icons.CACHED
        download_button.update()
        progress_bar.value = None
        progress_bar.update()

        # URL入力チェック
        if url_input.value == "":
            log_output.controls.append(Text("❌ URLを入力してください", weight=FontWeight.BOLD, color=Colors.RED))
            log_output.update()
            download_button.disabled = False
            download_button.text = "実行"
            download_button.icon = Icons.PLAY_ARROW
            download_button.update()
            progress_bar.value = 0
            progress_bar.update()
            return
        
        # yt-dlpコマンドの基本設定
        command = [
            "yt-dlp",
            "--newline",
            f"{url_input.value}",
            "--embed-metadata", "--add-metadata",
            "--default-search", "ytsearch",
            "--progress-template", "[DOWNLOADING]:%(progress._percent_str)s",
            "--add-header", "Accept-Language:ja-JP",
            "--extractor-args", "youtube:lang=ja",
            "--no-warnings"
        ]

        # Cookie設定の追加
        if cookie_source_dropdown.value == "file":
            if cookie_file_path == None:
                log_output.controls.extend([
                    Text("❌ Cookieファイルが選択されていません", weight=FontWeight.BOLD, color=Colors.RED),
                    Text("Cookieを使用せずダウンロードします", color=Colors.RED)
                ])
                log_output.update()
            else:
                command.extend(["--cookies", cookie_file_path])
        elif cookie_source_dropdown.value == "firefox":
            command.extend(["--cookies-from-browser", "firefox"])

        # 出力形式と品質設定
        if format_dropdown.value == "mp4":
            command.extend(["--merge-output-format", "mp4"])
            if quality_dropdown.value != "auto":
                if compatibility_checkbox.value:
                    command.extend(["-f", f"bestvideo[height<={quality_dropdown.value}][vcodec^=avc1]+bestaudio[ext=m4a]/best[height<={quality_dropdown.value}][vcodec^=avc1]/best[height<={quality_dropdown.value}]"])
                else:
                    command.extend(["-f", f"bestvideo[height<={quality_dropdown.value}]+bestaudio[ext=m4a]/best[height<={quality_dropdown.value}]"])
            else:
                if compatibility_checkbox.value:
                    command.extend(["-f", "bestvideo[vcodec^=avc1]+bestaudio[ext=m4a]/best[vcodec^=avc1]/best"])
                else:
                    command.extend(["-f", "bestvideo+bestaudio[ext=m4a]/best"])
        elif format_dropdown.value == "mkv":
            command.extend(["--merge-output-format", "mkv"])
            if quality_dropdown.value != "auto":
                if compatibility_checkbox.value:
                    command.extend(["-f", f"bestvideo[height<={quality_dropdown.value}][vcodec^=avc1]+bestaudio[ext=m4a]/best[height<={quality_dropdown.value}][vcodec^=avc1]/best[height<={quality_dropdown.value}]"])
                else:
                    command.extend(["-f", f"bestvideo[height<={quality_dropdown.value}]+bestaudio[ext=m4a]/best[height<={quality_dropdown.value}]"])
            else:
                if compatibility_checkbox.value:
                    command.extend(["-f", "bestvideo[vcodec^=avc1]+bestaudio[ext=m4a]/best[vcodec^=avc1]/best"])
                else:
                    command.extend(["-f", "bestvideo+bestaudio[ext=m4a]/best"])
        elif format_dropdown.value == "mp3":
            command.extend(["-f", "bestaudio", "-x", "--audio-format", "mp3"])
            if quality_dropdown.value != "auto":
                command.extend(["--audio-quality", quality_dropdown.value])
            else:
                command.extend(["--audio-quality", "0"])
        else:
            command.extend(["-f", "bestaudio", "-x", "--audio-format", format_dropdown.value, "--audio-quality", "0"])

        if hdr_checkbox.value:
            command.extend(["--format-sort", "hdr,res,codec,ext,size"])
        
        # 追加オプションの設定
        if chapter_checkbox.value:
            command.extend(["--embed-chapters", "--add-chapters"])
        
        if concurrent_connections_input.value != "" and concurrent_connections_input.value != "0":
            command.extend(["-N", str(concurrent_connections_input.value)])

        # 出力パスの設定
        if playlist_checkbox.value:
            command.extend(["-o", download_directory + "%(playlist_title)s/%(playlist_index)03d_%(title)s.%(ext)s"])
        else:
            command.extend(["-o", download_directory + "%(title)s.%(ext)s"])
        
        # サムネイル設定
        if thumbnail_checkbox.value:
            command.extend(["--embed-thumbnail", "--convert-thumbnails", "jpg"])
            if thumbnail_crop_checkbox.value:
                command.extend(["--ppa", "ThumbnailsConvertor:-qmin 1 -q:v 1 -vf crop=\"'if(gt(ih,iw),iw,ih)':'if(gt(iw,ih),ih,iw)'\""])
        
        # ログ設定
        timestamp = datetime.datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
        log_filename = os.path.join("./logs", f"{timestamp}.log")
        logging.basicConfig(
            filename=log_filename,
            level=logging.INFO,
            format="%(asctime)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        
        # コマンド実行の開始
        log_output.controls.extend([
            Text("📝 次のコマンドを実行します:", weight=FontWeight.BOLD),
            Text(" ".join(command), color=Colors.BLUE)
        ])
        log_output.update()

        try:
            # プロセスの実行
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            download_process = process

            # 出力の処理
            while True:
                output = process.stdout.readline()
                if output == "" and process.poll() is not None:
                    break
                
                if output:
                    output = output.strip()
                    if "[DOWNLOADING]" in output:
                        progress = output.split(":")[1].strip()
                        progress_bar.value = float(progress.strip("%")) / 100
                        progress_bar.update()
                    else:
                        log_output.controls.append(Text(output))
                        log_output.scroll_to(offset=-1)
                        log_output.update()
                        progress_bar.value = None
                        progress_bar.update()
                        logging.info(output)

            # エラー出力の収集
            errors = process.stderr.read()
            
            # プロセスの終了を待機
            return_code = process.wait()

            # エラー出力の表示
            if errors:
                log_output.controls.append(Text("❌ 発生したエラー:", weight=FontWeight.BOLD, color=Colors.RED))
                for error_line in errors.splitlines():
                    logging.error(error_line)
                    log_output.controls.append(Text(error_line, color=Colors.RED))
                    log_output.scroll_to(offset=-1)
                log_output.update()

            # 処理結果の表示
            if return_code == 0 and not errors:
                log_output.controls.append(Text("✅ 正常に終了しました。", color=Colors.GREEN))
                log_output.scroll_to(offset=-1)
                log_output.update()
                progress_bar.value = 1
                progress_bar.update()
            else:
                log_output.controls.append(Text("❌ エラーが発生しました", color=Colors.RED))
                log_output.scroll_to(offset=-1)
                log_output.update()
                progress_bar.value = 0
                progress_bar.update()

        except Exception as e:
            log_output.controls.append(Text(f"❌ 予期せぬエラーが発生しました: {str(e)}", color=Colors.RED))
            log_output.scroll_to(offset=-1)
            log_output.update()
            progress_bar.value = 0
            progress_bar.update()

        finally:
            # UIの状態を元に戻す
            download_button.disabled = False
            download_button.text = "実行"
            download_button.icon = Icons.PLAY_ARROW
            download_button.update()
            download_process = None

    def handle_output_directory_select(e: FilePickerResultEvent):
        """
        保存先ディレクトリの選択処理
        Args:
            e (FilePickerResultEvent): ファイルピッカーの結果イベント
        """
        nonlocal download_directory
        download_directory = os.path.normpath(e.path if e.path else download_directory) + os.path.sep
        output_directory_field.value = download_directory
        output_directory_field.update()
        
        # 設定の保存
        settings['download_directory'] = download_directory
        save_settings(settings)
    
    def handle_cookie_file_select(e: FilePickerResultEvent):
        """
        Cookieファイルの選択処理
        Args:
            e (FilePickerResultEvent): ファイルピッカーの結果イベント
        """
        nonlocal cookie_file_path
        if e.files:
            cookie_file_path = os.path.normpath(e.files[0].path)
        cookie_file_field.value = cookie_file_path if cookie_file_path else ""
        cookie_file_field.update()
        
        # 設定の保存
        settings['cookie_file_path'] = cookie_file_path
        save_settings(settings)

    def handle_settings_change(e):
        """
        設定変更時の処理
        Args:
            e: イベントオブジェクト
        """
        # 現在の設定を保存
        current_settings = {
            'download_directory': download_directory,
            'cookie_file_path': cookie_file_path,
            'format': format_dropdown.value,
            'quality': quality_dropdown.value,
            'concurrent_connections': concurrent_connections_input.value,
            'playlist_mode': playlist_checkbox.value,
            'thumbnail_embed': thumbnail_checkbox.value,
            'thumbnail_crop': thumbnail_crop_checkbox.value,
            'chapter_embed': chapter_checkbox.value,
            'cookie_source': cookie_source_dropdown.value,
            'compatibility_mode': compatibility_checkbox.value,
            'hdr_mode': hdr_checkbox.value
        }
        save_settings(current_settings)

    # ファイルピッカーの初期化
    output_directory_picker = FilePicker(on_result=handle_output_directory_select)
    cookie_file_picker = FilePicker(on_result=handle_cookie_file_select)
    page.overlay.append(output_directory_picker)
    page.overlay.append(cookie_file_picker)
    
    # UIコンポーネントの定義
    url_input = TextField(label="ダウンロード対象のURL", prefix_icon=Icons.LINK, hint_text="https://youtube.com/watch?v=...", expand=True, autofocus=True)
    paste_button = IconButton(icon=Icons.PASTE, on_click=handle_url_paste, tooltip="クリップボードから貼り付け")
    output_directory_field = TextField(value=download_directory, label="保存先フォルダ", expand=True, read_only=True, prefix_icon=Icons.FOLDER)
    select_directory_button = TextButton(text="フォルダ選択", icon=Icons.FOLDER_OPEN, on_click=lambda _: output_directory_picker.get_directory_path(dialog_title="保存先を選択", initial_directory=os.path.expanduser("~")))
    cookie_source_dropdown = Dropdown(
        label="Cookie取得元",
        options=[dropdown.Option(key="none", text="なし"), dropdown.Option(key="file", text="ファイル"), dropdown.Option(key="firefox", text="Firefox")],
        value=settings.get('cookie_source', 'none'),
        on_change=lambda e: [handle_cookie_source_change(e), handle_settings_change(e)]
    )
    cookie_file_field = TextField(
        label="Cookieファイル(.txt)",
        value=cookie_file_path if cookie_file_path else "",
        expand=True,
        read_only=True,
        prefix_icon=Icons.COOKIE
    )
    select_cookie_button = TextButton(text="ファイル選択", icon=Icons.FILE_OPEN, on_click=lambda _: cookie_file_picker.pick_files(dialog_title="Cookieファイルを選択", allow_multiple=False, allowed_extensions=["txt"]), tooltip="Cookieファイルを選択")
    cookie_file_row = Row([cookie_file_field, select_cookie_button], visible=cookie_source_dropdown.value == "file", alignment=MainAxisAlignment.START)
    log_output = Column(controls=[Text("📃 ダウンロードログ", weight=FontWeight.BOLD, size=16), Divider(), Text("ここにログが表示されます", weight=FontWeight.BOLD)], scroll=ScrollMode.AUTO, spacing=2, height=float("inf"), width=float("inf"), expand=True)
    format_dropdown = Dropdown(
        label="保存する拡張子",
        options=file_format_options,
        value=settings.get('format', file_format_options[0].key),
        expand=True,
        on_change=lambda e: [handle_format_change(e), handle_settings_change(e)],
        tooltip="保存するファイルの拡張子を選択します"
    )
    quality_dropdown = Dropdown(
        label="品質",
        options=video_quality_options,
        value=settings.get('quality', video_quality_options[0].key),
        expand=True,
        on_change=handle_settings_change,
        tooltip="一部の拡張子の品質を選択します\n自動の場合は自動で選択された品質でダウンロードします"
    )
    concurrent_connections_input = TextField(
        value=settings.get('concurrent_connections', "3"),
        label="同時接続数 (0~16)",
        tooltip="同時接続数を指定します\n0の場合は無効化します",
        on_change=lambda e: [validate_concurrent_connections(e), handle_settings_change(e)]
    )
    playlist_checkbox = Checkbox(
        label="プレイリストモード",
        value=settings.get('playlist_mode', False),
        on_change=handle_settings_change,
        tooltip="プレイリストをダウンロードする際に使うと便利です"
    )
    thumbnail_checkbox = Checkbox(
        label="サムネイルを埋め込む",
        value=settings.get('thumbnail_embed', False),
        on_change=lambda e: [handle_thumbnail_crop_toggle(e), handle_settings_change(e)],
        tooltip="サムネイルを埋め込みます"
    )
    thumbnail_crop_checkbox = Checkbox(
        label="サムネイルをクロッピング",
        value=settings.get('thumbnail_crop', False),
        disabled=not thumbnail_checkbox.value,
        on_change=handle_settings_change,
        tooltip="サムネイルを1:1にクロッピングします\n有効にするには\"サムネイルを埋め込む\"を有効にしてください"
    )
    chapter_checkbox = Checkbox(
        label="チャプターを埋め込む",
        value=settings.get('chapter_embed', False),
        on_change=handle_settings_change,
        tooltip="動画にチャプターを埋め込みます\nデフォルトで詳細なメタデータを埋め込むため場合によってはデフォルトで埋め込まれる場合があります"
    )
    compatibility_checkbox = Checkbox(
        label="互換性重視",
        value=settings.get('compatibility_mode', False),
        on_change=handle_settings_change,
        tooltip="より広い互換性を持つH.264などを優先します\nAV1の代わりにVP9やH.264などを優先します"
    )
    hdr_checkbox = Checkbox(
        label="HDRを優先する",
        value=settings.get('hdr_mode', False),
        on_change=handle_settings_change,
        tooltip="HDRを優先します\nHDRを優先する場合は\"互換性重視\"を無効にしてください"
    )
    download_button = ElevatedButton(text="実行", icon=Icons.PLAY_ARROW, on_click=execute_download, width=float("inf"), style=ButtonStyle(bgcolor=Colors.BLUE, color=Colors.WHITE, padding=padding.symmetric(vertical=16)))
    progress_bar = ProgressBar(value=0, border_radius=border_radius.all(8))

    # 左パネル（設定パネル）のレイアウト
    settings_panel = Column(
        controls=[
            Row([Text(page.title, size=28, weight=FontWeight.BOLD), Text(f"v{VERSION}", color=Colors.BLACK45, size=12)]),
            Row([url_input,paste_button]),
            Row([output_directory_field, select_directory_button]),
            Row([format_dropdown, quality_dropdown]),
            cookie_source_dropdown,
            cookie_file_row,
            concurrent_connections_input,
            Column([
                Text("オプション", weight=FontWeight.BOLD, size=15),
                chapter_checkbox,
                playlist_checkbox,
                thumbnail_checkbox,
                thumbnail_crop_checkbox,
                compatibility_checkbox,
                hdr_checkbox
            ], spacing=2),
            progress_bar,
            download_button
        ],
        spacing=14,
        width=420,
        scroll=ScrollMode.AUTO,
        alignment=MainAxisAlignment.START,
        height=float("inf"),
        horizontal_alignment=CrossAxisAlignment.START
    )

    # 右パネル（ログ表示）のレイアウト
    log_panel = Container(
        content=log_output,
        border=border.all(2, Colors.BLUE_200),
        border_radius=border_radius.all(10),
        padding=12,
        expand=True,
        height=float("inf"),
        bgcolor=Colors.WHITE
    )

    # メインレイアウトの設定
    page.add(
        Row(
            [
                settings_panel,
                log_panel
            ],
            spacing=12,
            expand=True
        )
    )

# アプリケーションの起動
app(target=main)