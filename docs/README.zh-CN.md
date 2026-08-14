# Silico Grove Image Skill

[English](../README.md) | [繁體中文](README.zh-TW.md) | [日本語](README.ja.md) | [Español](README.es.md) | [Русский](README.ru.md) | [한국어](README.ko.md)

## 复制给你的 AI

将下面这段提示词交给 AI Agent，即可安装并使用 Silico Grove 生图 Skill。

```text
请安装并使用这个 Silico Grove 生图 Skill：
https://github.com/Rodert/silicogrove-image-skill

首次使用时请主动提示我输入 Silico Grove API Key，并自动安全保存到本机配置中，之后直接读取使用；不要要求我手动配置环境变量。

请使用异步图片任务；图片生成完成后下载到我的本地输出目录，而不只是展示图片链接。

每次 generate 或 edit 请求前，请检查此 Skill 的上游 Git 更新。没有更新时静默继续；发现更新时，请明确提醒我更新可能包含必要的修复，本地检出干净时先快进更新再发起图片请求。检查或更新失败，或本地修改阻止更新时，请提示我且不要发起请求；绝不覆盖本地修改。

请为所选模型使用其所属公司对应分组的 API Key。不要假定控制台分组名称固定；确认所选模型对已保存的 Key 可用。若生图失败，请提示我检查该公司对应分组的 Key、模型权限和余额。

使用文档：
https://docs.silicogrove.com/zh-cn/api/#images
```
