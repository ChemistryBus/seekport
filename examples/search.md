## 1. Search | DeepSeek API Docs
<https://api-docs.deepseek.com/api/search/>

DeepSeek · score 2.414104461669922 · auth 3

## https://api.deepseek.com/v1/tools/search
...
Default value:10
...
need_content boolean
...
Whether to return page content incontent. Defaults to false; when false, content is always an empty string.
...
The page content. Empty whenneed_content is false or when the content is unavailable.

---

## 2. Search | DeepSeek API Docs - Search / Fetch API is now available, powered by our in-house search engine and supporting web search and fetch
<https://api-docs.deepseek.com/api/search/#1>

DeepSeek · score 2.414104461669922 · auth 3

## https://api.deepseek.com/v1/tools/search
...
need_content boolean

Whether to return page content incontent. Defaults to false; when false, content is always an empty string.
...
The page content. Empty whenneed_content is false or when the content is unavailable.

---

## 3. https://api.deepseek.com/v1/tools/search
<https://api-docs.deepseek.com/zh-cn/api/search/>

DeepSeek · score 2.382854461669922 · auth 3

## https://api.deepseek.com/v1/tools/search
...
Default value:10
...
need_content boolean
...
是否在content 中返回网页正文。默认为 false；为 false 时，content 恒为空字符串。
...
网页正文。need_content 为 false 或正文缺失时为空字符串。

---

## 4. deepseek-websearch-mcp
<https://www.npmjs.com/package/deepseek-websearch-mcp#1>

NPM · 2026-10-16 · score 2.34179243844882 · auth 3

# deepseek-websearch-mcp
...
#### webSearch(query, count?, freshness?
...
, localization?, need_content?)

参数 | 说明 
---|---
ori_question | 可选，触发搜索的用户原始问题（官方字段，辅助意图理解） 
localization | 可选，用于优先返回本地化结果的 IP 地址（官方字段） 
need_content | 是否返回页面全文，默认 false 只返回摘要

---

## 5. web_search
<https://github.com/kohaku-lab/kohakuterrarium/blob/9465beeb76be43db0f8f082b70cebea2065d404e/src/kohakuterrarium/builtin_skills/tools/web_search.md>

GitHub · 2026-10-22 · score 2.34179243844882 · auth 3

# web_search
...
## Arguments

| Arg | Type | Req | Description |
| --- | --- | --- | --- |
| need_content | boolean | no | deepseek_api only: include page content; omitted/null uses the tool setting (false) |
...
- Other backends ignore false/null `need_content` and empty/null `ori_question`.
