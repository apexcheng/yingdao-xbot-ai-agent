---
name: code-consistency
description: Maintain implementation consistency when modifying or adding code in an existing project. Use when similar logic, API usage, control flow, error handling, logging, or data processing may already exist in the repository.
---

# 代码实现一致性

修改或新增已有项目代码时，先从当前项目学习已有实现，不为同类问题重新设计另一套等价写法。

## 修改前

先搜索与当前任务相同或最接近的实现。

搜索顺序：

1. 当前文件和相邻代码。
2. 当前模块。
3. 当前项目其它模块。

重点比较：

- 使用哪个 API。
- 元素 / 数据如何查询。
- 存在性如何判断。
- 控制流使用 `if`、循环还是异常。
- 异常如何处理。
- 日志如何记录。
- 返回值和数据结构如何组织。
- 局部代码是链式调用还是保留变量。

先按业务问题找相近实现，再判断项目原本采用了什么写法；不要先决定实现方式，再只搜索支持该写法的代码。

## 有成熟先例时

场景相同时，沿用已有实现模式。

不要仅因为另一种写法同样正确，就引入第二套表达方式。

例如当前项目同类场景已经统一使用：

```python
elements = element.find_all_by_xpath(xpath)
if elements:
    ...
```

则不要无业务原因改成：

```python
try:
    element.find_by_xpath(xpath)
except Exception:
    ...
```

两种代码都可能运行，但存在性判断、API 选择和控制流已经不同。以上仅用于说明“实现漂移”，不表示所有场景都必须使用 `find_all_by_xpath`。

## 没有成熟先例时

当前项目找不到相近实现时，再按项目 `AGENTS.md` 查询知识库、真实参考项目或 API 文档。

不要为了保持一致而模仿明显错误、已经废弃或与当前场景不同的代码。

## 项目存在多种写法时

不要顺手统一整个项目。

优先级：

1. 当前文件或当前模块正在使用的成熟写法。
2. 与当前业务场景最接近的实现。
3. 项目中较新的、仍在使用的实现。

如果无法判断哪一种属于当前约定，再根据知识库选择，不扩大本次修改范围。

## 修改后

检查本次新增或修改的代码与附近同类实现。

如果出现新的 API 选择、判断方式、异常处理方式、日志模式、数据处理模式或局部代码结构，确认这种差异是否有实际业务或技术原因。

没有原因，就改回项目已有模式。

## 例外

用户明确要求重构、统一风格、替换旧模式或优化已有实现时，不机械沿用旧代码。
