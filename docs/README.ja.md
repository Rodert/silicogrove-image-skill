# Silico Grove Image Skill

[English](../README.md) | [简体中文](README.zh-CN.md) | [繁體中文](README.zh-TW.md) | [Español](README.es.md) | [Русский](README.ru.md) | [한국어](README.ko.md)

## AI にコピー

次のプロンプトを AI Agent に渡して、Silico Grove Image Skill をインストールして使用してください。

```text
この Silico Grove Image Skill をインストールして使用してください:
https://github.com/Rodert/silicogrove-image-skill

初回使用時に Silico Grove API Key の入力を自発的に求め、ローカル設定に安全に保存してください。以後のリクエストでは自動的に再利用し、環境変数を手動設定するよう求めないでください。

非同期の画像タスクを使用し、完成した画像はリンクだけを表示せず、ローカル出力ディレクトリにダウンロードしてください。

毎日最初の generate または edit リクエストの前に、この Skill の上流 Git 更新を確認し、その日の後続リクエストでは確認をスキップしてください。更新がない場合は通知せず続行してください。更新が見つかった場合は簡潔に知らせ、ローカルのチェックアウトがクリーンなら画像リクエストの前に fast-forward で更新してください。確認または更新に失敗した場合、またはローカルの変更が更新を妨げる場合は、簡潔に知らせてインストール済みバージョンでリクエストを続行してください。ローカルの変更は決して上書きしないでください。

選択したモデルの提供会社に対応するグループの API Key を使用してください。コンソールのグループ名が固定だと仮定せず、保存済み Key でモデルが利用可能か確認してください。生成に失敗した場合は、提供会社に対応する Key グループ、モデル権限、残高を確認するよう案内してください。

公式ドキュメント:
https://docs.silicogrove.com/zh-cn/api/#images
```
