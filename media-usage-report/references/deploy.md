# 发布到 Netlify

将生成的 HTML 部署到 Netlify（也可类推到 Vercel / GitHub Pages）。

## 准备

- 安装 Netlify 插件：`codex plugin add "netlify@openai-curated"`（可能需要提权写插件缓存）。
- 安装 Netlify CLI 到临时目录（Windows 上 `npm install netlify-cli --ignore-scripts` 可绕开 esbuild 二进制问题）：

```bash
npm install netlify-cli --no-audit --no-fund --ignore-scripts
```

## 登录

用 ticket 流程避免密码传递：

```bash
netlify login --request "部署媒体使用报告" --json
# 输出 Ticket ID 与 Authorize URL；把 URL 给用户，授权后：
netlify login --check <ticket-id>
```

验证：`netlify status` 应显示邮箱与 Team。

## 部署

```bash
# 准备发布目录，把 HTML 复制为 index.html
mkdir deploy && cp media-usage-report.html deploy/index.html

# 创建站点
netlify sites:create --name <site-name> --json

# 生产部署
netlify deploy --dir deploy --site <site-id> --prod --json
```

返回的 `url` 即线上地址；用 `netlify api getDeploy --data '{"deploy_id":"..."}'` 确认 `state: "ready"`。

## 访问问题排查

部署成功但浏览器打不开时，先区分「部署问题」与「网络问题」：

- 用 `curl -I https://<site>.netlify.app` 验证线上状态；返回 200 说明部署正常。
- 用户网络有代理时（如 Clash），站点解析到的海外 IPv4 可能被阻断而 IPv6 可通：
  - `curl -4` / `curl -6` 分别测试，对比 remote_ip 与超时情况；
  - 让用户在代理中把站点域名加入代理规则，或换网络环境访问。
- 后台 `app.netlify.com` 能开但站点打不开，通常是边缘 IP 连通性问题，不是部署问题。
