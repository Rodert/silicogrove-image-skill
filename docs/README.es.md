# Silico Grove Image Skill

[English](../README.md) | [简体中文](README.zh-CN.md) | [繁體中文](README.zh-TW.md) | [日本語](README.ja.md) | [Русский](README.ru.md) | [한국어](README.ko.md)

## Copia para tu IA

Entrega el siguiente mensaje a un agente de IA para instalar y usar Silico Grove Image Skill.

```text
Instala y utiliza este Silico Grove Image Skill:
https://github.com/Rodert/silicogrove-image-skill

En el primer uso, pídeme de forma proactiva una Silico Grove API Key y guárdala de forma segura en mi configuración local. Reutilízala automáticamente en solicitudes posteriores. No me pidas configurar una variable de entorno.

Usa tareas de imagen asíncronas y descarga las imágenes terminadas en mi directorio local de salida, no solo enlaces de imágenes.

Antes de la primera solicitud generate o edit de cada día, comprueba las actualizaciones Git remotas de este Skill y omite la comprobación en las siguientes solicitudes del mismo día. Si no hay actualización, continúa sin avisarme. Si hay una actualización, avísame brevemente y actualiza una copia local limpia antes de hacer la solicitud de imagen. Si falla la comprobación o la actualización, o los cambios locales la bloquean, avísame y no hagas la solicitud; no sobrescribas nunca los cambios locales.

Usa una API Key del grupo correspondiente al proveedor del modelo seleccionado. No supongas que el nombre del grupo en la consola es fijo; confirma que el modelo está disponible para la Key guardada. Si la generación falla, indícame que verifique el grupo de Key del proveedor, el acceso al modelo y el saldo.

Documentación oficial:
https://docs.silicogrove.com/zh-cn/api/#images
```
