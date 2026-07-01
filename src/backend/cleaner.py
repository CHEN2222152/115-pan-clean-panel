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

    def verify(self) -> dict:
        r = self.session.get(f"{self.API_BASE}/user/info", timeout=15)
        if not r.ok:
            return {"state": False, "error": f"HTTP {r.status_code}"}
        try:
            data = r.json()
        except Exception as e:
            return {"state": False, "error": f"JSON parse error: {e}"}
        if not isinstance(data, dict):
            return {"state": False, "error": f"Unexpected type: {type(data).__name__}, content: {str(data)[:200]}"}
        return data

    def search_received_files(self, limit: int = 200) -> List[Dict]:
        params = {
            "receive": "1",
            "offset": 0,
            "limit": limit,
            "type": 1,
            "source": "user",
            "order": "user_ptime",
            "asc": 0,
            "aid": 1,
            "show_dir": 0,
            "format": "json",
        }
        r = self.session.get(f"{self.API_BASE}/files/search", params=params, timeout=15)
        if not r.ok:
            return []
        try:
            data = r.json()
            if isinstance(data, dict) and data.get("state"):
                return data.get("data", [])
        except:
            pass
        return []

    def delete_files(self, file_ids: List[str]) -> dict:
        payload = {f"fid[{i}]": fid for i, fid in enumerate(file_ids)}
        r = self.session.post(f"{self.API_BASE}/files/delete", data=payload, timeout=15)
        try:
            data = r.json()
            return data if isinstance(data, dict) else {"state": False}
        except:
            return {"state": False}

    def empty_recycle_bin(self) -> dict:
        r = self.session.post(f"{self.API_BASE}/rb/empty", timeout=60)
        try:
            data = r.json()
            return data if isinstance(data, dict) else {"state": False}
        except:
            return {"state": False}

    def clean_received(self, max_files: int = 200) -> dict:
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
            "message": f"deleted {len(file_ids)} files" if result.get("state") else "删除失败",
            "detail": result,
        }

    def clean_recycle_bin(self) -> dict:
        result = self.empty_recycle_bin()
        return {
            "success": result.get("state"),
            "message": "回收站已清空" if result.get("state") else "清空回收站失败",
            "detail": result,
        }
