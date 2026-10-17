# 《遗落之境的继承者》GBA 简体中文补丁

对应用户提供的 **Inheritors of the Oubliette v1.2**。原 ROM 未改动。请打开 `output/inheritors_zh.gba` 游玩，或者把 `output/inheritors_zh.bps` 应用到完全相同的原版 ROM。

## 汉化范围

- 243 条游戏文本：135 条剧情、教程、战斗、状态、菜单、结局及制作人员标题；108 条灵晶、灵术、装备名称和说明。
- 标题标志、开始游戏／读取存档／系统设置、设置界面图形按钮、战斗未中提示一并汉化。
- 6 条作者署名、版权品牌、分隔符或调试文字明确保留。按键 A/B/L/R/START、数值和单位等保留。
- 对话和物品说明用原生 **12px Fusion Pixel 简体中文点阵字**，紧凑的战斗、属性、存档、菜单提示用 **8px**。保持原有调色板与阴影。
- 标题中文名为本补丁译名，原题为 Inheritors of the Oubliette。

## 安装与存档

1. 直接加载 `output/inheritors_zh.gba`，或用支持 BPS 的补丁工具生成 ROM。
2. BPS 必须匹配下列原版 SHA-256：
   `1d8b4617be75a8b7b6c5c2975ef0213ed37da669c460d967d4259b6a25d22b2e`
3. 游戏本身的保存逻辑、存档结构及五个存档位均未修改。模拟器通常按 ROM 文件名寻找 `.sav`；使用原有存档时请先保留备份，再把副本命名成中文 ROM 对应的名字。原英文存档的预览标签可能仍为英文，重新保存会生成中文标签。
4. 中文 ROM 写出的存档预览使用自定义编码，直接用英文 ROM 查看时标签可能乱码；这里没有承诺英文版对中文预览标签的显示兼容性。

## 验证

使用 mGBA 0.10.5 核心，对最终 ROM 实施：

- 正常启动、标题选项、进入游戏、移动触发开场剧情六段、装备详情、系统设置，以及正常菜单写入存档；截图见 `analysis/runtime/`。
- 单独的 RAM 场景夹具调用原版 `force_fixed_encounter(0)` 进入一场实际战斗，验证攻击、选敌及灵术选择菜单。夹具仅影响测试模拟器的临时内存，不写入发行 ROM。
- 249 条记录的字体宽度核验；596 个中文／标点字形分别在 8px、12px 下完成 **1,192 次逐像素核验**。
- 全部剧情、教程和灵术说明通过可见行数限制核验。
- 原文件 SHA-256、GBA 头校验、32MiB 地址范围、最终 ROM 与运行报告哈希一致；BPS 生成后独立重建结果与最终 ROM 完全一致。

这不是全流程通关或真机测试；隐藏流程、所有战斗组合、旧存档恢复未逐一验证。战斗场景使用明确标注的 RAM 夹具，不能当作正常路线通关的证据。

最终 ROM 的 SHA-256：
`33a35095e159721710d6a4da375f87fe80fd6ba00cc551899821ee381d884f77`

## 实现与复现

采用对用户 ROM 的补丁，而非重新编译替换整个游戏，保留原版游戏逻辑、声音与素材。二进制原文、引用、译文见 `analysis/coverage.json`。

- 覆盖原 `text_width`（0x08006090）、`draw_text`（0x080060C0）、`wrap_text`（0x0800A8F4）；替换为支持自定义双字节编码的字宽、绘制、中文断行。
- 静态字符串追加到 ROM 并修正编译器引用；固定长度的物品数据原位替换并验证字段容量。
- 12px 对话采用 12px 行距，三行说明采用 14px 行距，避免原 8px 高度产生覆盖或末行裁切。
- 直接绘制到原对象字形画布，边界为 256×128；没有为汉化增加堆内存或持久 RAM 缓存。
- 字库采用 **Fusion Pixel Font / SIL OFL 1.1**，见 `licenses/Fusion-Pixel-OFL.txt`。

当前共享工作区复现命令：

```sh
python3 INHERITORS/tools/build_zh.py
python3 INHERITORS/tools/check_runtime.py
python3 GBA_TRANSLATION_BATCH/package_verify.py INHERITORS INHERITORS/output/inheritors_zh.gba --runtime INHERITORS/analysis/runtime/report.json --scope '243条文本、图形及12px/8px字库；见README验证范围'
```

构建脚本复用本工作区 `ANGUNA/assets/fonts/` 和 `POWDER/toolchain/xpack-arm-none-eabi-gcc-15.2.1-1.1/`。运行验证的 `runtime_bridge.dylib` 仅用于测试，不包含在 ROM 中。修改工具与译文已保留在 `tools/`、`translations/`。

## 来源和许可证

- 官方源码：[DrLancer-X/inheritors-of-the-oubliette](https://github.com/DrLancer-X/inheritors-of-the-oubliette)，本地参考提交 `f7ec9dc63cad6a627a5549a2b0c417795095d609`；2026-10-11 在线核实。字库、数据和图形文件与提供的 ROM 逐字节匹配。
- 游戏源码采用 GPL-3.0，许可证见 `licenses/Game-GPL-3.0.txt`。署名 Mahou Shoujo ☆ Magical Moestar / one60hp 保留。
- 逆向流程参考 REA skill；当前 REA `open_binary` 对原始 GBA 镜像不支持，因此本游戏使用官方源码辅助、ARM/Thumb 静态反汇编及模拟器证据。
