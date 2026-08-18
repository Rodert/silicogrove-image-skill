# Silico Grove Image Skill

[English](../README.md) | [简体中文](README.zh-CN.md) | [日本語](README.ja.md) | [Español](README.es.md) | [Русский](README.ru.md) | [한국어](README.ko.md)

## 複製給你的 AI

將下列提示詞交給 AI Agent，即可安裝並使用 Silico Grove 生圖 Skill。

```text
請安裝並使用這個 Silico Grove 生圖 Skill：
https://github.com/Rodert/silicogrove-image-skill

首次使用時請主動提示我輸入 Silico Grove API Key，並自動安全儲存到本機設定中，之後直接讀取使用；不要要求我手動設定環境變數。

請使用非同步圖片任務；圖片生成完成後下載到我的本機輸出目錄，而不只是顯示圖片連結。

每天第一次 generate 或 edit 請求前檢查此 Skill 的上游 Git 更新，當天後續請求跳過檢查。沒有更新時保持靜默；發現更新時簡短提醒我，並在本機檢出乾淨時先快進更新再發起圖片請求。檢查或更新失敗，或本機修改阻止更新時，請提示我且不要發起請求；絕不覆蓋本機修改。

請為所選模型使用其所屬公司對應分組的 API Key。不要假定控制台分組名稱固定；確認所選模型對已儲存的 Key 可用。若生圖失敗，請提示我檢查該公司對應分組的 Key、模型權限和餘額。

使用文件：
https://docs.silicogrove.com/zh-cn/api/#images
```
