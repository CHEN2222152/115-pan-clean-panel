import requests
import json
from typing import List, Dict


class Pan115Cleaner:
    API_BASE = "https://webapi.115.com"
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Origin": "https://115.com",
        "Referer": "https://115.com/",
    }

    def __init__(self, cookies: dict):
        self.session = requests.Session()
        self.session.cookies.update(cookies)
        self.session.headers.update(self.HEADERS)

    # ────────── 验证 ──────────

    def _is_success(self, data: dict) -> bool:
        if "state" in data:
            return bool(data["state"])
        return data.get("errno") == 0

    def verify(self) -> dict:
        r = self.session.get(f"{self.API_BASE}/user/info", timeout=15)
        if not r.ok:
            return {"state": False, "error": f"HTTP {r.status_code}"}
        try:
            data = r.json()
        except Exception as e:
            return {"state": False, "error": f"JSON parse error: {e}"}
        if not isinstance(data, dict):
            return {"state": False, "error": f"Unexpected type: {type(data).__name__}"}
        return data

    # ────────── 最近接收文件 ──────────

    def search_received_files(self, limit: int = 200) -> List[Dict]:
        """搜索最近接收文件 — 尝试多种参数组合"""
        param_sets = [
            {"receive": "1", "offset": 0, "limit": limit, "type": 1, "source": "user",
             "order": "user_ptime", "asc": 0, "aid": 1, "show_dir": 0, "format": "json"},
            {"receive": "1", "offset": 0, "limit": limit, "type": 1, "source": "user",
             "order": "user_ptime", "asc": 0, "format": "json"},
            {"offset": 0, "limit": limit, "type": 1, "source": "user",
             "order": "user_ptime", "asc": 0, "format": "json"},
        ]
        for params in param_sets:
            try:
                r = self.session.get(f"{self.API_BASE}/files/search", params=params, timeout=15)
                if not r.ok:
                    continue
                data = r.json()
                if isinstance(data, dict):
                    # 兼容多种成功响应格式
                    if self._is_success(data):
                        items = data.get("data") or data.get("rows") or data.get("list") or []
                        if isinstance(items, list) and len(items) > 0:
                            return items
            except:
                continue

        # 兜底: 尝试其他端点
        for endpoint in ["/receive/list", "/box/receive"]:
            try:
                r = self.session.get(f"{self.API_BASE}{endpoint}", timeout=15)
                if r.ok:
                    data = r.json()
                    if isinstance(data, dict) and self._is_success(data):
                        items = data.get("data") or data.get("rows") or data.get("list") or []
                        if isinstance(items, list) and len(items) > 0:
                            return items
            except:
                continue

        return []

    def delete_files(self, file_ids: List[str]) -> dict:
        """批量删除文件"""
        payload = {f"fid[{i}]": fid for i, fid in enumerate(file_ids)}
        r = self.session.post(f"{self.API_BASE}/files/delete", data=payload, timeout=15)
        try:
            data = r.json()
            return data if isinstance(data, dict) else {"state": False}
        except:
            return {"state": False}

    def clean_received(self, max_files: int = 200) -> dict:
        """清理最近接收文件"""
        files = self.search_received_files(limit=max_files)
        if not files:
            return {"success": True, "deleted": 0, "message": "没有需要清理的接收文件"}
        file_ids = [f.get("fid") or f.get("file_id") for f in files]
        file_ids = [fid for fid in file_ids if fid]
        if not file_ids:
            return {"success": True, "deleted": 0, "message": "未找到可删除的文件 ID"}
        result = self.delete_files(file_ids)
        return {
            "success": result.get("state"),
            "deleted": len(file_ids),
            "message": f"已删除 {len(file_ids)} 个接收文件" if result.get("state") else "删除接收文件失败",
            "detail": result,
        }

    # ────────── 回收站 ──────────

    def list_recycle_bin_files(self, limit: int = 500):
        """列出回收站中的文件, 返回 (文件列表, 错误信息)"""
        params = {"offset": 0, "limit": limit}
        try:
            r = self.session.get(f"{self.API_BASE}/rb/list", params=params, timeout=15)
            if not r.ok:
                return [], f"HTTP {r.status_code}"
            data = r.json()
            if isinstance(data, dict) and self._is_success(data):
                items = data.get("data") or data.get("rows") or []
                return (items if isinstance(items, list) else []), ""
            if isinstance(data, dict):
                err = data.get("error", "") or data.get("errMsg", "")
                return [], err
        except Exception as e:
            return [], str(e)
        return [], ""

    def delete_recycle_files(self, file_ids: List[str]) -> dict:
        """从回收站中永久删除指定文件"""
        payload = {f"fid[{i}]": fid for i, fid in enumerate(file_ids)}
        r = self.session.post(f"{self.API_BASE}/rb/delete", data=payload, timeout=30)
        try:
            data = r.json()
            return data if isinstance(data, dict) else {"state": False}
        except:
            return {"state": False}

    def clean_recycle_bin(self) -> dict:
        """清空回收站 — 检测到 115 服务不可用时跳过无用重试"""
        # 1) 列出回收站文件逐个删除
        files, err_info = self.list_recycle_bin_files(limit=500)
        if files:
            file_ids = [f.get("fid") or f.get("file_id") for f in files]
            file_ids = [fid for fid in file_ids if fid]
            if file_ids:
                result = self.delete_recycle_files(file_ids)
                if result.get("state"):
                    return {"success": True, "deleted": len(file_ids),
                            "message": f"回收站已清空 ({len(file_ids)} 个文件)", "detail": result}
                return {"success": False, "message": "逐个删除回收站文件失败", "detail": result}

        # 如果 /rb/list 明确返回服务不可用，直接返回，跳过重试
        if err_info and "开小差" in err_info:
            return {"success": False, "message": "回收站API暂时不可用，稍后再试", "detail": err_info}

        # 2) 兜底: 直接调用批量清空
        for payload in [{}, {"type": 1}, {"all": 1}]:
            try:
                r = self.session.post(f"{self.API_BASE}/rb/empty", data=payload, timeout=60)
                result = r.json()
                if isinstance(result, dict) and self._is_success(result):
                    return {"success": True, "message": "回收站已清空", "detail": result}
            except:
                continue

        return {"success": False, "message": "清空回收站失败", "detail": "all methods failed"}
