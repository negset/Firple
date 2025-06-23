# Firple Sample Images

README.md やウェブサイトで使用する。

## SVG 作成方法

1. Inkscape で SVG 作成
2. テキストエディタで `font-feature-settings` 等を修正

## WebP 作成方法

### 要求物

- Node.js
- Firple

フォントをローカルにインストールしておく必要がある。

### コマンド

- セットアップ

  ```
  $ git clone https://github.com/negset/svg-to-webp
  $ npm install --prefix svg-to-webp
  ```

- 変換

  ```
  $ node svg-to-webp *.svg
  ```
