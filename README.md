# shuifeng

## 审计智能体引导式访问设计

本仓库当前交付一套“去掉左侧菜单栏，改为引导式访问”的设计稿，图片尺寸为 `1980x1080`。

- [设计说明](docs/guided-access-design.md)
- [引导式总入口](designs/00-guided-entry.svg)
- [智能识别工作流](designs/01-smart-recognition.svg)
- [审计数据接入工作流](designs/02-data-ingestion.svg)
- [审计方法全流程工作流](designs/03-method-workflow.svg)

如需重新生成设计资产，运行：

```bash
python3 scripts/generate_design_assets.py
```

## PNG 图片预览

### 1. 引导式总入口

![引导式总入口](images/00-guided-entry.png)

### 2. 智能识别工作流

![智能识别工作流](images/01-smart-recognition.png)

### 3. 审计数据接入工作流

![审计数据接入工作流](images/02-data-ingestion.png)

### 4. 审计方法全流程工作流

![审计方法全流程工作流](images/03-method-workflow.png)
