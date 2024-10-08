# プログラミング向けフォント Firple

[Fira Code](https://github.com/tonsky/FiraCode) と [IBM Plex Sans JP](https://github.com/IBM/plex) を
合成したプログラミング向け日本語フォントです。

![Firple サンプル](https://github.com/negset/Firple/raw/images/sample-top.png)

## 特徴

- 豊富なグリフ

  Fira Code が持つグリフを全てそのまま使用できます。  
  加えて、日本語文字や一部記号を IBM Plex Sans JP のグリフで補っています。

- 字幅を 1:2 に調整

  半角文字と全角文字の横幅の比を 1:2 に揃えています。

- リガチャ対応

  Fira Code が持つプログラミング向けのリガチャを利用できます。

- 2 種のウェイト

  Regular と Bold の 2 ウェイトを提供しています。

- 独自のイタリック体

  Firple 独自の字形を持ったイタリック体を提供しています。

- Slim サブファミリー

  Fira Code の字幅を縮小した Slim サブファミリーを提供しています。

- Nerd Fonts 対応

  [Nerd Fonts](https://www.nerdfonts.com/) の多彩なグリフを含んでいます。

## フォント機能

OpenType features による字形の変更に対応しています。  
対応するエディタで設定を変更することで、以下の機能を使用できます。  
(各種エディタにおける有効化方法は、[FiraCode のドキュメント](https://github.com/tonsky/FiraCode/wiki/How-to-enable-stylistic-sets) を参照してください。)

またフォント生成時に `--freeze-features` オプションを指定することで、これらの機能を標準で有効化できます。

- 全角スペース可視化 (`cv33`)

  全角スペースを可視化して、意図せぬ混入を防ぎます。

- 半濁点の強調 (`ss11`)

  半濁点を強調して、濁点と判別しやすくします。

![OpenType features サンプル](https://github.com/negset/Firple/raw/images/sample-features.png)

## フォントファミリー

### Firple

Fira Code の英字をそのまま利用できます。日本語の文字に字間のゆとりが生まれます。

|フォント名         |説明                                     |
|:------------------|:----------------------------------------|
|Firple Regular     |Fira Code Regular + IBM Plex Sans JP Text|
|Firple Italic      |Firple Regular のイタリック体            |
|Firple Bold        |Fira Code Bold + IBM Plex Sans JP Bold   |
|Firple Bold Italic |Firple Bold のイタリック体               |

### Firple Slim

Fira Code の字幅を縮小しています。1 行に多くの文字を表示でき、日本語文字が自然な字間になります。

|フォント名             |説明                           |
|:----------------------|:------------------------------|
|Firple Slim Regular    |Firple Regular の字幅縮小版    |
|Firple Slim Italic     |Firple Italic の字幅縮小版     |
|Firple Slim Bold       |Firple Bold の字幅縮小版       |
|Firple Slim Bold Italic|Firple Bold Italic の字幅縮小版|

## サンプル

[こちら](https://negset.com/Firple/#sample) で任意のテキストの表示を確認できます。

## ダウンロード

以下のボタンからフォントをダウンロードできます。

<a href="https://github.com/negset/Firple/releases" target="_blank" rel="noopener noreferrer">
  <img alt="ダウンロード" src="https://img.shields.io/github/downloads/negset/Firple/total?style=for-the-badge&logo=github&color=485fc7">
</a>

## ライセンス

[SIL Open Font License (OFL) Version 1.1](https://github.com/negset/Firple/blob/master/LICENSE.txt)

## ビルド

- 環境

  Ubuntu 22.04.3 LTS で確認

- 必要パッケージ

  ```sh
  $ sudo apt install fontforge python3-fontforge fonttools ttfautohint
  ```

- ビルドコマンド

  ```sh
  $ make setup
  $ make all
  ```

  または

  ```sh
  $ ./downloader.py --all
  $ ./firple.py --all
  ```

  スクリプトのコマンドラインオプションは `--help` で確認できます。
