# NeCd
![header](image/necd-header.svg)

> [!WARNING]
> 来月(4月)中盤をめどに既存のいくつかの類似リポジトリをアーカイブします。  
> 今後のアップデートは行われません。

## 概要
YouTubeから動画をダウンロードするコマンドラインツール`yt-dlp`のGUIフロントエンドです。  
制作者が必要だなって思った機能と過去のﾉｳﾊｳみたいなものを使って新しく書きました。

削れたものもあります。

## 機能
### 拡張子・品質
拡張子はmp4,mp3,mkv,opus,flacから選択できるように。  
その他の拡張子はあまり使わないでしょってことで追加しません。

品質はmp4,mkvはHD(720p)～4K(2160p)を選択可能、  
mp3の場合は128kbps～320kbpsを選択可能です。  
その他については自動で最高音質のものが選ばれます。

### Cookie
拡張機能を用いてダウンロードしたtxtファイルとFirefoxから読み込むの2つの方法です。  
後者はFirefoxベースの派生ブラウザだと動かないかも。

### 同時接続
`yt-dlp`の`-N`オプションをデフォルトで有効化。  
0にすることで無効にでき、接続数は16まで指定可能。

### プレイリストモード
プレイリストに適したオプションにします。  
といっても保存先をちょいといじるだけですが。

### サムネイル
サムネイルの埋め込みと1:1へのクロップを選択できます。  
後者は音楽を落とすときにいいかもしれません。

## 動作確認済み
いずれもpythonは3.10.x
| OS | Binary | .py | メモ |
|---|---|---|-----|
|Windows 10 Pro 22H2 | ⭕ | ⭕ | 変換などにffmpegが必要なので要インストール |
|ArchLinux | ⭕ | ⭕ | クリップボード関係は`xclip`のインストールが必要 |
|macOS 15 | ❌️ | ⭕ | pyinstallerでバイナリにしたら動かない。 |

なおWindows向け以外の実行可能ファイルの配布は行わない(環境の差異が顕著に出るため)  
ソースからpyinstallerを使い実行可能ファイルにすること。

## 必要なもの
このソフトウェアは以下のものが必要です。
- **Python**  
  ソフト自体の起動はできるがyt-dlpの動作には欠かせないため要インストール。  
  開発・確認はPython 3.10.xxで行っています。

- **yt-dlp**  
  絶対必要!!インストールは以下のコマンドを実行します(要Python)
  ```bash
  pip install yt-dlp
  ```

- **ffmpeg**  
  変換やマージ、サムネイルの埋め込みなどyt-dlpがファイルに対して行う操作全部に必要なのでインストールしよう。  
  インストール方法はググってください。

## トラブルシュート
### opusやflacにメタデータを埋め込もうとするとエラーが出る
一部のコーデックへのメタデータやカバーを埋め込む際には`mutagen`が必要になります。  
以下のコマンドでインストールできます。
```bash
pip install mutagen
```
### 「正常に完了しました」と出たのにエラーログが出る
これは仕様です。  
エラーではなく警告もstderrで出力されているため起こることです。  
ログの一番最後に「✅ 正常に完了しました。」と出れば大丈夫です。

## スクショ
![](image/README-2025-3-25.webp)

![](image/README-2025-3-25_1.webp)

![](image/README-2025-3-25_2.webp)