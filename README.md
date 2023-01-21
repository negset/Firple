# プログラミング向けフォント Firple

Firple は、[Fira Code](https://github.com/tonsky/FiraCode) と [IBM Plex Sans JP](https://github.com/IBM/plex) を合成したプログラミング向けフォントです。

![Firple Regular サンプル](https://github.com/negset/Firple/raw/images/sample.png)

## 特徴

- 豊富なグリフ

  Fira Code が持つグリフを全てそのまま使用できます。  
  また日本語文字などは、IBM Plex Sans JP のグリフで補っています。

- 字幅を 1:2 に調整

  半角文字と全角文字の横幅の比を 1:2 に揃えています。

- リガチャに対応

  Fira Code が持つプログラミング向けのリガチャを利用できます。

- 2 種のウェイト

  Regular と Bold の 2 ウェイトがあります。

- 独自のイタリック体

  Fira Code には無い独自の字形を持ったイタリック体があります。

- Slim サブファミリー

  Fira Code の字幅を縮小した Slim サブファミリーを提供しています。

## フォントファミリー

### Firple

|フォント名         |説明                                     |
|:------------------|:----------------------------------------|
|Firple Regular     |Fira Code Regular + IBM Plex Sans JP Text|
|Firple Italic      |Firple Regular のイタリック体            |
|Firple Bold        |Fira Code Bold + IBM Plex Sans JP Bold   |
|Firple Bold Italic |Firple Bold のイタリック体               |

### Firple Slim

|フォント名             |説明                           |
|:----------------------|:------------------------------|
|Firple Slim Regular    |Firple Regular の字幅縮小版    |
|Firple Slim Italic     |Firple Italic の字幅縮小版     |
|Firple Slim Bold       |Firple Bold の字幅縮小版       |
|Firple Slim Bold Italic|Firple Bold Italic の字幅縮小版|

## ライセンス

[SIL Open Font License (OFL) Version 1.1](https://github.com/negset/Firple/blob/master/LICENSE.txt)

## ダウンロード

[Releases ページ](https://github.com/negset/Firple/releases) から入手できます。

## ビルド

### 必要なもの

- FontForge および fontTools

```
$ sudo apt install fontforge
$ sudo apt install fonttools
```

- 元となるフォントファイル

```
src/FiraCode-Bold.ttf
src/FiraCode-Regular.ttf
src/IBMPlexSansJP-Bold.ttf
src/IBMPlexSansJP-Text.ttf
```

### コマンド

```
$ ./run.sh
```