# Silico Grove Image Skill

Languages: [English](README.md) | [简体中文](docs/README.zh-CN.md) | [繁體中文](docs/README.zh-TW.md) | [日本語](docs/README.ja.md) | [Español](docs/README.es.md) | [Русский](docs/README.ru.md) | [한국어](docs/README.ko.md)

## Copy for your AI

Give the following prompt to an AI Agent to install and use the Silico Grove Image Skill.

```text
Install and use this Silico Grove Image Skill:
https://github.com/Rodert/silicogrove-image-skill

On first use, proactively ask me for a Silico Grove API Key and save it securely in my local configuration. Reuse it automatically for later requests. Do not ask me to configure an environment variable.

Use asynchronous image tasks and download completed images to my local output directory, not only as image links.

Before every generate or edit request, silently check this Skill's upstream Git update when no update is available. If an update is available, explicitly tell me it may contain required fixes, then update a clean checkout before making the image request. If the check or update fails, or local changes block the update, tell me and do not make the request; never overwrite local changes.

Choose an API Key from the group for the selected model's provider. Do not assume the console's group name follows a fixed naming convention. Confirm the selected model is available to the saved Key; if image generation fails, tell me to verify the provider's Key group, model access, and balance.

Official documentation:
https://docs.silicogrove.com/zh-cn/api/#images
```
