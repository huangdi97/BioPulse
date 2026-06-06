# Management · 管理端

> 企业管理后台。总裁/经理/员工三级权限视图，仪表盘、员工管理、角色配置。

**端口：** 8011

## 核心文件

| 文件 | 说明 |
|:-----|:-----|
| `app/main.py` | 应用入口 |
| `app/president_router.py` | 总裁视图（全局只读仪表盘） |
| `app/manager_router.py` | 经理视图（部门管理+操作） |
| `app/employee_router.py` | 员工视图（个人数据） |
| `app/dashboard_router.py` | 仪表盘 API |
| `app/services/` | 管理业务服务 |

## 启动

```bash
uvicorn management.app.main:app --port 8011
```
