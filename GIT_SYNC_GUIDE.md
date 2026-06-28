# Git 同步说明

本项目已初始化为 Git 仓库，默认分支为 `main`。原始 POI 数据较大，仓库使用 Git LFS 管理大文件。

## Mac 端首次推送

先在 GitHub / Gitee / GitLab 新建一个空仓库，不要勾选自动生成 README、`.gitignore` 或 License。

拿到远程仓库地址后执行：

```bash
git remote add origin <你的远程仓库URL>
git push -u origin main
```

如果远程平台支持 Git LFS，推送会同时上传以下大文件：

- `spike/data/poi_raw_all_food.jsonl`
- `spike/data/poi_raw_chicken_keyword.jsonl`
- `spike/data/poi_real_chicken.jsonl`
- `spike_chicken_gz.zip`

## Windows 端首次克隆

Windows 电脑需要先安装：

1. Git for Windows
2. Git LFS

然后执行：

```powershell
git lfs install
git clone <你的远程仓库URL>
cd <仓库目录>
git lfs pull
```

## 日常同步

每次在一台电脑上修改后：

```bash
git status
git add .
git commit -m "描述这次改动"
git push
```

另一台电脑开始工作前：

```bash
git pull
git lfs pull
```

## 注意

- 不要提交 `.venv/`、`__pycache__/`、`.DS_Store` 等本机文件，`.gitignore` 已排除。
- `spike/out_delivery/` 是给组员交付的干净数据包。
- `spike/data/` 保留原始采集数据，较大的 `.jsonl` 文件走 Git LFS。
- 如果远程平台不支持 LFS，原始大文件需要改用网盘同步，Git 仓库只保留脚本和清洗后的交付数据。
