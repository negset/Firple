# プログラミング向けフォント Firple

Firple は，Fira Code と IBM Plex Sans JP を合成したプログラミング向けフォントです．

![Firple Regular サンプル](https://github.com/negset/Firple/raw/images/sample.png)

## 特徴

- 豊富で美麗なグリフ

  Fira Code が持つグリフは全てそのまま利用できます．
  それ以外のグリフは IBM Plex Sans JP 由来のものが適用されます．

- 横幅を 1:2 に調整

  半角文字と全角文字の横幅の比が 1:2 に揃えてあります．

- リガチャに対応

  Fira Code 由来のコーディング向けリガチャが全てそのまま利用できます．

- 2 種のウェイト

  Regular と Bold の 2 ウェイトがあります．

## フォントファミリーの説明

フォント名    |説明
:-------------|:----------------------------------------
Firple Regular|Fira Code Regular + IBM Plex Sans JP Text
Firple Bold   |Fira Code Bold + IBM Plex Sans JP Bold

## ライセンス

[SIL Open Font License (OFL) Version 1.1](https://github.com/negset/Firple/blob/master/LICENSE.txt)

## ダウンロード

[Releases ページ](https://github.com/negset/Firple/releases) から入手できます．

## ビルド

### 必要なもの

- FontForge および fontTools

```
$ sudo apt install fontforge
$ sudo apt install fonttools
```

- 元となるフォントファイル

```
fonts/FiraCode-Bold.ttf
fonts/FiraCode-Regular.ttf
fonts/IBMPlexSansJP-Bold.ttf
fonts/IBMPlexSansJP-Text.ttf
```

### コマンド

```
$ ./build.sh
```